import sys
import time
import shutil
import datetime
import calendar
import cPickle as pickle
import threading
import traceback

from UserDict import DictMixin

from functools import wraps

import requests
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
from cachecontrol.heuristics import LastModified, TIME_FMT

from email.utils import formatdate, parsedate, parsedate_tz

from flask import g, request
from sqlalchemy.exc import IntegrityError
from labmanager.db import db
from labmanager.application import app
from labmanager.models import RLMSTypeCache, RLMSCache

class LastModifiedNoDate(LastModified):
    """ This takes the original LastModified implementation of 
    cachecontrol, but defaults the date in case it is not provided.
    """
    def __init__(self, require_date = True, error_margin = None):
        if error_margin is None:
            if require_date:
                self.error_margin = 0.1
            else:
                self.error_margin = 0.2
        else:
            self.error_margin = error_margin
        self.require_date = require_date

    def update_headers(self, resp):
        headers = resp.headers
        if 'expires' in headers:
            return {}

        if 'cache-control' in headers and headers['cache-control'] != 'public':
            return {}

        if resp.status not in self.cacheable_by_default_statuses:
            return {}

        if 'last-modified' not in headers:
            return {}

        parsed_date = parsedate_tz(headers.get('date'))
        if self.require_date and parsed_date is None:
            return {}
        
        if parsed_date is None:
            date = time.time()
            faked_date = True
        else:
            date = calendar.timegm(parsed_date)
            faked_date = False

        last_modified = parsedate(headers['last-modified'])
        if last_modified is None:
            return {}

        now = time.time()
        current_age = max(0, now - date)
        delta = date - calendar.timegm(last_modified)
        freshness_lifetime = max(0, min(delta * self.error_margin, 24 * 3600))
        if freshness_lifetime <= current_age:
            return {}

        expires = date + freshness_lifetime
        new_headers = {'expires': time.strftime(TIME_FMT, time.gmtime(expires))}
        if faked_date:
            new_headers['date'] = time.strftime(TIME_FMT, time.gmtime(date))
        return new_headers

    def warning(self, resp):
        return None

CACHE_DIR = 'web_cache'

def get_cached_session():
    sess = CacheControl(requests.Session(),
                    cache=FileCache(CACHE_DIR), heuristic=LastModifiedNoDate(require_date=False))

    original_get = sess.get
    def wrapped_get(*args, **kwargs):
        try:
            return original_get(*args, **kwargs)
        except (OSError, IOError) as e:
            return requests.get(*args, **kwargs)
    sess.get = wrapped_get
    return sess

def clean_cache():
    try:
        shutil.rmtree(CACHE_DIR)
    except (OSError, IOError) as e:
        pass

def context_wrapper(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            getattr(g, 'testing_if_running_in_context', None)
        except RuntimeError:
            running_inside_context = False
        else:
            running_inside_context = True

        if running_inside_context:
            return func(*args, **kwargs)
        
        with app.app_context():
            return func(*args, **kwargs)

    return wrapper

class CacheDisabler(object):

    def disable(self):
        AbstractCache.disable_cache()

    def reenable(self):
        AbstractCache.enable_cache()

    def __del__(self):
        AbstractCache.enable_cache()

    def __enter__(self):
        AbstractCache.disable_cache()

    def __exit__(self, *args, **kwargs):
        AbstractCache.enable_cache()

_MEMORY_CACHE = {
    # original_value: resulting_value
}

_FORCE_CACHE = threading.local()

def force_cache():
    _FORCE_CACHE.force = True

def dont_force_cache():
    _FORCE_CACHE.force = False

def is_forcing_cache():
    nocache = request.args.get('force_cache', '').lower()
    if nocache in ('true', '1'):
        return False
    return getattr(_FORCE_CACHE, 'force', False)

class AbstractCache(object, DictMixin):

    _local_ctx = threading.local()

    def __init__(self, context_id):
        self.context_id = context_id
        super(AbstractCache, self).__init__()

    @staticmethod
    def enable_cache():
        AbstractCache._local_ctx.cache_disabled = False

    @staticmethod
    def disable_cache():
        AbstractCache._local_ctx.cache_disabled = True

    @context_wrapper
    def get(self, key, default_value = None, min_time = datetime.timedelta(hours=1)):
        if getattr(AbstractCache._local_ctx, 'cache_disabled', False):
            return default_value

        # If the request says don't take into account the cache, do not do it
        try:
            headers = request.headers
        except RuntimeError:
            headers = {}

        if is_forcing_cache():
            print("[%s]: Cache ignore request by User agent %s from %s. Key: %s; context_id: %s" % (time.asctime(), headers.get('User-Agent'), headers.get('X-Forwarded-For'), key, self.context_id))
            sys.stdout.flush()
            return default_value

        now = datetime.datetime.now()
        oldest = now - min_time
        result = db.session.query(self.MODEL).filter(self.MODEL_CONTEXT_COLUMN() == self.context_id, self.MODEL.key == key, self.MODEL.datetime >= oldest).order_by(self.MODEL.datetime.desc()).first()
        if result is None:
            print("[%s]: Cache miss by User agent %s from %s. Key: %s; context_id: %s" % (time.asctime(), headers.get('User-Agent'), headers.get('X-Forwarded-For'), key, self.context_id))
            sys.stdout.flush()
            return default_value

        key = result.value
        if key in _MEMORY_CACHE:
            return _MEMORY_CACHE[key]

        try:
            decoded_value = result.value.decode('base64')
        except Exception as e:
            print("[%s]: Cache miss due to invalid base64 contents, by User agent %s from %s. Key: %s; context_id: %s" % (time.asctime(), headers.get('User-Agent'), headers.get('X-Forwarded-For'), key, self.context_id))
            sys.stdout.flush()
            _MEMORY_CACHE[key] = default_value
            return default_value

        
        try:
            result = pickle.loads(decoded_value)
        except:
            print("[%s]: Cache miss due to pickle request by User agent %s from %s. Key: %s; context_id: %s" % (time.asctime(), headers.get('User-Agent'), headers.get('X-Forwarded-For'), key, self.context_id))
            sys.stdout.flush()
            _MEMORY_CACHE[key] = None
            return None
        else:
            _MEMORY_CACHE[key] = result
            return result

    def __getitem__(self, key):
        default_value = object()
        result = self.get(key, default_value)
        if result == default_value:
            raise KeyError(key)

        return result

    @context_wrapper
    def __setitem__(self, key, value):
        existing_values = db.session.query(self.MODEL).filter(self.MODEL_CONTEXT_COLUMN() == self.context_id, self.MODEL.key == key).all()
        for existing_value in existing_values:
            db.session.delete(existing_value)
        new_record = self.MODEL(self.context_id, key = key, value = pickle.dumps(value).encode('base64'), datetime = datetime.datetime.now())
        db.session.add(new_record)
        try:
            db.session.commit()
        except IntegrityError:
            traceback.print_exc()
            db.session.rollback()
        except:
            traceback.print_exc()
            db.session.rollback()
            raise
        return value

    def keys(self):
        return [ key for key,  in db.session.query(self.MODEL.key).filter(self.MODEL_CONTEXT_COLUMN() == self.context_id).all() ]

    def __delitem__(self, key):
        results = db.session.query(self.MODEL).filter(self.MODEL_CONTEXT_COLUMN() == self.context_id, self.MODEL.key == key).all()
        found = False
        for result in results:
            found = True
            db.session.delete(result)
        
        if found:
            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise
        else:
            raise KeyError(key)

    @context_wrapper
    def clear(self, mix_time = datetime.timedelta(hours=24)):
        now = datetime.datetime.now()
        oldest = now - min_time
        existing_values = db.session.query(self.MODEL).filter(self.MODEL_CONTEXT_COLUMN() == self.context_id, self.MODEL.datetime < oldest).all()
        for value in existing_values:
            db.session.delete(value)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        except:
            db.session.rollback()
            raise

class GlobalCache(AbstractCache):
    MODEL = RLMSTypeCache
    MODEL_CONTEXT_COLUMN = lambda *args: RLMSTypeCache.rlms_type

    def __init__(self, rlms_type):
        super(GlobalCache, self).__init__(rlms_type)

class VersionCache(GlobalCache):
    def __init__(self, version_id):
        super(VersionCache, self).__init__(version_id)

class InstanceCache(AbstractCache):
    MODEL = RLMSCache
    MODEL_CONTEXT_COLUMN = lambda *args : RLMSCache.rlms_id

    def __init__(self, rlms_id):
        super(InstanceCache, self).__init__(rlms_id)

class EmptyCache(dict):
    def get(self, key, default_value = None, min_time = datetime.timedelta(hours=1)):
        return dict.get(self, key, default_value)

    def __setitem__(self, key, *args, **kwargs):
        print("Warning: using __setitem__ in empty cache with key {}".format(key))
        traceback.print_stack()
        return dict.__setitem__(self, key, *args, **kwargs)

import datetime
import calendar
import pickle

from UserDict import DictMixin

from functools import wraps

import requests
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
from cachecontrol.heuristics import LastModified, TIME_FMT

from email.utils import formatdate, parsedate, parsedate_tz

from flask import g
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

def get_cached_session():
    CACHE_DIR = 'web_cache'
    return CacheControl(requests.Session(),
                    cache=FileCache(CACHE_DIR), heuristic=LastModifiedNoDate(require_date=False))

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

class AbstractCache(object, DictMixin):
    def __init__(self, context_id):
        self.context_id = context_id
        super(AbstractCache, self).__init__()

    @context_wrapper
    def get(self, key, default_value = None, min_time = datetime.timedelta(hours=1)):
        now = datetime.datetime.now()
        oldest = now - min_time
        result = db.session.query(self.MODEL).filter(self.MODEL_CONTEXT_COLUMN() == self.context_id, self.MODEL.key == key, self.MODEL.datetime >= oldest).order_by(self.MODEL.datetime.desc()).first()
        if result is None:
            return default_value

        return pickle.loads(result.value)

    def __getitem__(self, key):
        default_value = object()
        result = self.get(key, default_value)
        if result == default_value:
            raise KeyError(key)

        return result

    @context_wrapper
    def __setitem__(self, key, value):
        existing_values = db.session.query(self.MODEL).filter_by(rlms_type=self.context_id, key=key).all()
        for existing_value in existing_values:
            db.session.delete(existing_value)
        new_record = self.MODEL(self.context_id, key = key, value = pickle.dumps(value), datetime = datetime.datetime.now())
        db.session.add(new_record)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        except:
            db.session.rollback()
            raise

    def keys(self):
        return [ key for key,  in db.session.query(self.MODEL.key).filter_by(rlms_type=self.context_id).all() ]

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


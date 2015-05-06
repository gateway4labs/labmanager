import datetime
import calendar
import pickle

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
from labmanager.models import RLMSTypeCache

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

class GlobalCache(object):
    def __init__(self, rlms_type):
        self.rlms_type = rlms_type

    @context_wrapper
    def get(self, key, default_value = None, min_time = datetime.timedelta(hours=1)):
        now = datetime.datetime.now()
        oldest = now - min_time
        result = db.session.query(RLMSTypeCache).filter(RLMSTypeCache.rlms_type == self.rlms_type, RLMSTypeCache.key == key, RLMSTypeCache.datetime >= oldest).order_by(RLMSTypeCache.datetime.desc()).first()
        if result is None:
            return default_value

        return pickle.loads(result.value)

    @context_wrapper
    def save(self, key, value):
        existing_values = db.session.query(RLMSTypeCache).filter_by(rlms_type=self.rlms_type, key=key).all()
        for value in existing_values:
            db.session.delete(value)
        new_record = RLMSTypeCache(rlms_type = self.rlms_type, key = key, value = pickle.dumps(value), datetime = datetime.datetime.now())
        db.session.add(new_record)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        except:
            db.session.rollback()
            raise

    @context_wrapper
    def clean_cache(self, mix_time = datetime.timedelta(hours=24)):
        now = datetime.datetime.now()
        oldest = now - min_time
        existing_values = db.session.query(RLMSTypeCache).filter(RLMSTypeCache.rlms_type == self.rlms_type, RLMSTypeCache.datetime < oldest).all()
        for value in existing_values:
            db.session.delete(value)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        except:
            db.session.rollback()
            raise


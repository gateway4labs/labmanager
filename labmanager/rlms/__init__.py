# -*-*- encoding: utf-8 -*-*-
# 
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import sys
import time
import threading
import datetime
import traceback
import requests


from labmanager.db import db
from labmanager.models import RLMS as dbRLMS
from labmanager.application import app
from .base import register_blueprint, BaseRLMS, BaseFormCreator, Capabilities, Versions
from .caches import GlobalCache, VersionCache, InstanceCache, EmptyCache, get_cached_session, CacheDisabler, clean_cache

assert BaseFormCreator or register_blueprint or Versions or Capabilities or BaseRLMS or True # Avoid pyflakes warnings

# 
# Add the proper managers by pointing to a module
# 

_RLMSs = {
    # "RLMS type" :  <module>, 

    # e.g.
    # "WebLab-Deusto" : ( labmanager.rlms.ext.weblabdeusto, ['4.0'], record ),
}

_GLOBAL_PERIODIC_TASKS = [
    # {
    #     'name' : "WebLab-Deusto",
    #     'versions' : ["4.0", "5.0"],
    #     'func' : func,
    #     'when' : datetime.timedelta
    # }
]

_LOCAL_PERIODIC_TASKS = [
    # {
    #     'name' : "WebLab-Deusto",
    #     'versions' : ["4.0", "5.0"],
    #     'func' : func,
    #     'when' : datetime.timedelta
    # }
]


class Laboratory(object):
    def __init__(self, name, laboratory_id, description = None, autoload = False):
        self.name          = name
        self.laboratory_id = laboratory_id
        self.description   = description
        self.autoload      = autoload

    def __repr__(self):
        return "Laboratory(%r, %r, %r, %r)" % (self.name, self.laboratory_id, self.description, self.autoload)

    def __hash__(self):
        return hash(self.laboratory_id)


_current_task_id = 0
def _next_task_id():
    global _current_task_id
    _current_task_id += 1
    return _current_task_id

class _RegistrationRecord(object):
    def __init__(self, name, versions):
        self.name = name
        self.versions = versions
        global_key = '%s - %s' % (name, ', '.join(versions))
        self.global_cache = self.cache = GlobalCache(global_key)
        self.per_version_cache = {}
        for version in versions:
            # If a single version it's supported, the global cache is the same as the per version cache
            version_key = '%s - %s' % (name, version)
            self.per_version_cache[version] = VersionCache(version_key)
        
        self.per_thread = threading.local()

    def get_cache(self, version = None):
        if version is None:
            return self.cache
        else:
            return self.version_cache[version]

    @property
    def rlms_cache(self):
        current_rlms_id = getattr(self.per_thread, 'current_rlms_id', None)
        if current_rlms_id is not None:
            return InstanceCache(current_rlms_id)
        else:
            return EmptyCache()

    @property
    def cached_session(self):
        cached_session = getattr(self.per_thread, 'cached_session', None)
        if cached_session:
            return cached_session

        cached_session = get_cached_session()
        self.per_thread.cached_session = cached_session

        def timeout_get(url, timeout = (30, 60), max_retries = 3, **kwargs):
            count = 0
            while True:
                try:
                    return cached_session.get(url, timeout = timeout, **kwargs)
                except requests.Timeout:
                    count += 1
                    if count >= max_retries:
                        raise
        
        cached_session.timeout_get = timeout_get
        return cached_session

    def _add_periodic_task(self, where, task_name, function, hours, minutes, disable_cache):
        if hours == 0 and minutes == 0:
            raise ValueError("You must establish hours or minutes")

        if hours < 0 or minutes < 0:
            raise ValueError("hours and minutes must be positive numbers")

        where.append({
            'id'   : _next_task_id(),
            'name' : task_name,
            'rlms' : self.name,
            'versions' : self.versions,
            'func' : function,
            'when' : datetime.timedelta(hours = hours, minutes = minutes),
            'disable_cache' : disable_cache,
        })

    def add_global_periodic_task(self, task_name, function, hours = 0, minutes = 0, disable_cache = True):
        return self._add_periodic_task(_GLOBAL_PERIODIC_TASKS, task_name, function, hours, minutes, disable_cache)

    def add_local_periodic_task(self, task_name, function, hours = 0, minutes = 0, disable_cache = True):
        return self._add_periodic_task(_LOCAL_PERIODIC_TASKS, task_name, function, hours, minutes, disable_cache)

    def is_debug(self):
        return 'debug' in sys.argv or '-debug' in sys.argv or '--debug' in sys.argv

def _debug(msg):
    sys.stderr.flush()
    sys.stdout.flush()
    print u"[%s] - %s" % (time.ctime(), msg)
    sys.stdout.flush()
    sys.stderr.flush()

class TaskRunner(object):
    def __init__(self):
        # task_id : datetime.datetime
        self.latest_executions = {
        }
        self._stopping = False

    def _now(self):
        return datetime.datetime.now().replace(second = 0, microsecond = 0)

    def _must_be_run(self, now, task):
        if task['id'] not in self.latest_executions:
            return True

        time_elapsed = now - self.latest_executions[task['id']]
        if time_elapsed >= task['when']:
            return True

        return False

    def _run_all(self):
        # Run global tasks
        cache_disabler = CacheDisabler()

        for task in _GLOBAL_PERIODIC_TASKS:
            now = self._now()
            if self._must_be_run(now, task):
                for version in task['versions']:
                    _debug("Running task %r for rlms %s %s..." % (task['name'], task['rlms'], version))
                    if task['disable_cache']:
                        cache_disabler.disable()
                    try:
                        task['func']()
                    except Exception:
                        traceback.print_exc()
                    finally:
                        cache_disabler.reenable()

                self.latest_executions[task['id']] = now

        # Same for regular
        for task in _LOCAL_PERIODIC_TASKS:
            now = self._now()
            if self._must_be_run(now, task):
                with app.app_context():
                    for version in task['versions']:
                        rlmss = db.session.query(dbRLMS).filter_by(kind = task['rlms'], version = version).all()
                        for db_rlms in rlmss:
                            ManagerClass = get_manager_class(db_rlms.kind, db_rlms.version, db_rlms.id)
                            rlms = ManagerClass(db_rlms.configuration)
                            _debug(u"Running task %r for rlms %s %s (%s)..." % (repr(task['name']), repr(task['rlms']), repr(version), repr(db_rlms.location)))
                            if task['disable_cache']:
                                cache_disabler.disable()

                            try:
                                task['func'](rlms)
                            except Exception:
                                traceback.print_exc()
                            finally:
                                cache_disabler.reenable()

                self.latest_executions[task['id']] = now

    def _step(self, initial):
        before = self._now()
        if before.hour == initial.hour and before.minute == initial.minute:
            clean_cache()

        future = before + datetime.timedelta(minutes = 1)
        future = future.replace(second = 0, microsecond = 0)
        self._run_all()
        after = datetime.datetime.now()

        remaining_seconds = (future - after).total_seconds()
        if remaining_seconds > 0:
            PIECES = 60
            per_second = remaining_seconds / PIECES
            for _ in xrange(PIECES):
                if self._stopping:
                    break
                time.sleep(per_second)
        else:
            print "Warning: the last run_all took: %s time" % (after - before).total_seconds()

    def run_forever(self):
        initial = self._now()
        while not self._stopping:
            self._step(initial)

    def stop(self):
        self._stopping = True

def register(name, versions, module_name):
    record = _RegistrationRecord(name, versions)
    _RLMSs[name] = (module_name, versions, record)
    return record

def get_supported_types():
    return _RLMSs.keys()
        
def get_supported_versions(rlms_type):
    if rlms_type in _RLMSs:
        _, versions, _ = _RLMSs[rlms_type]
        return versions
    return []

def is_supported(rlms_type, rlms_version):
    _, versions, _ = _RLMSs.get(rlms_type, (None, []))
    return rlms_version in versions

def _get_module(rlms_type, rlms_version):
    module_name, versions, _ = _RLMSs.get(rlms_type, (None, []))
    if rlms_version in versions:
        if hasattr(sys.modules[module_name], 'get_module'):
            return sys.modules[module_name].get_module(rlms_version)
        else:
            return sys.modules[module_name]
    else:
        raise Exception(u"Misconfiguration: %(rlmstype)s %(rmlsversion)s does not exist" % dict(rlmstype = rlms_type, rmlsversion = rlms_version))

def _get_form_creator(rlms_type, rlms_version):
    return _get_module(rlms_type, rlms_version).FORM_CREATOR

def get_form_class(rlms_type, rlms_version):
    form_creator = _get_form_creator(rlms_type, rlms_version)
    return form_creator.get_add_form()

def get_permissions_form_class(rlms_type, rlms_version):
    form_creator = _get_form_creator(rlms_type, rlms_version)
    return form_creator.get_permission_form()

def get_lms_permissions_form_class(rlms_type, rlms_version):
    form_creator = _get_form_creator(rlms_type, rlms_version)
    return form_creator.get_lms_permission_form()

def get_manager_class(rlms_type, rlms_version, current_rlms_id = None):
    module = _get_module(rlms_type, rlms_version)
    _, _, record = _RLMSs[rlms_type]
    if current_rlms_id:
        record.per_thread.current_rlms_id = current_rlms_id
    return module.RLMS


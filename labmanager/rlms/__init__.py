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

from labmanager.application import app
from labmanager.db import db
from .base import register_blueprint, BaseRLMS, BaseFormCreator, Capabilities, Versions
from .caches import GlobalCache, VersionCache, get_cached_session

assert BaseFormCreator or register_blueprint or Versions or Capabilities or BaseRLMS or True # Avoid pyflakes warnings

# 
# Add the proper managers by pointing to a module
# 

_RLMSs = {
    # "RLMS type" :  <module>, 

    # e.g.
    # "WebLab-Deusto" : ( labmanager.rlms.ext.weblabdeusto, ['4.0'] ),
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

class _RegistrationRecord(object):
    def __init__(self, name, versions):
        self.name = name
        self.versions = versions
        global_key = '%s - %s' % (name, ', '.join(versions))
        self.cache = GlobalCache(global_key)
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
    def cached_session(self):
        cached_session = getattr(self.per_thread, 'cached_session', None)
        if cached_session:
            return cached_session

        cached_session = get_cached_session()
        self.per_thread.cached_session = cached_session
        return cached_session

    def _add_periodic_task(self, where, task_name, function, hours, minutes):
        if hours == 0 and minutes == 0:
            raise ValueError("You must establish hours or minutes")

        if hours < 0 or minutes < 0:
            raise ValueError("hours and minutes must be positive numbers")

        where.append({
            'name' : task_name,
            'rlms' : self.name,
            'versions' : self.versions,
            'func' : function,
            'when' : datetime.timedelta(hours = hours, minutes = minutes),
        })

    def add_global_periodic_task(self, task_name, function, hours = 0, minutes = 0):
        return self._add_periodic_task(_GLOBAL_PERIODIC_TASKS, task_name, function, hours, minutes)

    def add_local_periodic_task(self, task_name, function, hours = 0, minutes = 0):
        return self._add_periodic_task(_LOCAL_PERIODIC_TASKS, task_name, function, hours, minutes)

def _debug(msg):
    sys.stderr.flush()
    sys.stdout.flush()
    print "[%s] - %s" % (time.ctime(), msg)
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

    def _run_all(self):
        # Run global tasks
        for task_id, task in enumerate(_GLOBAL_PERIODIC_TASKS):
            now = self._now()
            must_be_run = False
            if task_id not in self.latest_executions:
                must_be_run = True
            else:
                time_elapsed = now - self.latest_executions[task_id]
                if time_elapsed >= task['when']:
                    must_be_run = True

            if must_be_run:
                for version in task['versions']:
                    _debug("Running task %r for rlms %s %s..." % (task['name'], task['rlms'], version))
                    try:
                        task['func']()
                    except Exception:
                        traceback.print_exc()
                self.latest_executions[task_id] = now

        # Same for regular
        for task_id, task in enumerate(_LOCAL_PERIODIC_TASKS):
            now = self._now()
            must_be_run = False
            if task_id not in self.latest_executions:
                must_be_run = True
            else:
                time_elapsed = now - self.latest_executions[task_id]
                if time_elapsed >= task['when']:
                    must_be_run = True

            if must_be_run:
                with app.app_context():
                    for version in task['versions']:
                        rlmss = db.session.query(RLMS).filter_by(kind = task['rlms'], version = version).all()
                        for db_rlms in rlmss:
                            ManagerClass = get_manager_class(db_rlms.rlms_type, db_rlms.rlms_version)
                            rlms = ManagerClass(db_rlms.configuration)
                            _debug("Running task %r for rlms %s %s (%s)..." % (task['name'], task['rlms'], version, db_rlms.location))
                            try:
                                task['func'](rlms)
                            except Exception:
                                traceback.print_exc()

                self.latest_executions[task_id] = now

    def _step(self):
        before = self._now()
        future = before + datetime.timedelta(minutes = 1)
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

    def run_forever(self):
        while not self._stopping:
            self._step()

    def stop(self):
        self._stopping = True

def register(name, versions, module_name):
    _RLMSs[name] = (module_name, versions)
    return _RegistrationRecord(name, versions)

def get_supported_types():
    return _RLMSs.keys()
        
def get_supported_versions(rlms_type):
    if rlms_type in _RLMSs:
        _, versions = _RLMSs[rlms_type]
        return versions
    return []

def is_supported(rlms_type, rlms_version):
    _, versions = _RLMSs.get(rlms_type, (None, []))
    return rlms_version in versions

def _get_module(rlms_type, rlms_version):
    module_name, versions = _RLMSs.get(rlms_type, (None, []))
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

def get_manager_class(rlms_type, rlms_version):
    module = _get_module(rlms_type, rlms_version)
    return module.RLMS

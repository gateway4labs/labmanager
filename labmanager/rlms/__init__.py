# -*-*- encoding: utf-8 -*-*-
# 
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import sys

from .base import register_blueprint, BaseRLMS, BaseFormCreator, Capabilities, Versions
assert BaseFormCreator or register_blueprint or Versions or Capabilities or BaseRLMS or True # Avoid pyflakes warnings

# 
# Add the proper managers by pointing to a module
# 

_RLMSs = {
    # "RLMS type" :  <module>, 

    # e.g.
    # "WebLab-Deusto" : ( labmanager.rlms.ext.weblabdeusto, ['4.0'] ),
}

class Laboratory(object):
    def __init__(self, name, laboratory_id):
        self.name          = name
        self.laboratory_id = laboratory_id

    def __hash__(self):
        return hash(self.laboratory_id)

def register(name, versions, module_name):
    _RLMSs[name] = (module_name, versions)

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
        return sys.modules[module_name].get_module(rlms_version)
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

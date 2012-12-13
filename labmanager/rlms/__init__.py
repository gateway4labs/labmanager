# -*-*- encoding: utf-8 -*-*-
# 
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
  :copyright: 2012 Pablo Orduña, Elio San Cristobal, Alberto Pesquera Martín
  :license: BSD, see LICENSE for more details
"""

import sys

# 
# Add the proper managers by pointing to a module
# 

_RLMSs = {
    # "RLMS type" :  <module>, 

    # e.g.
    # "WebLab-Deusto" : ( labmanager.rlms.ext.weblabdeusto, ['4.0'] ),
}

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
        raise Exception("Misconfiguration: %s %s does not exist" % (rlms_type, rlms_version))

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

"""
This module provides a Fake RLMS for performing unit tests. 
It is not registered by default. Call register_fake() to register it.
"""

import sys
import json

from labmanager.forms import AddForm, RetrospectiveForm, GenericPermissionForm
from labmanager.data import Laboratory
from labmanager.rlms import register
from labmanager.rlms.base import BaseRLMS, BaseFormCreator

def get_module(version):
    return sys.modules[__name__]

class FakeAddForm(AddForm):
    
    def __init__(self, add_or_edit, *args, **kwargs):
        super(FakeAddForm, self).__init__(*args, **kwargs)
        self.add_or_edit = add_or_edit

class FakePermissionForm(RetrospectiveForm):
    pass

class FakeLmsPermissionForm(FakePermissionForm, GenericPermissionForm):
    pass

class FakeFormCreator(BaseFormCreator):
    def get_add_form(self):
        return FakeAddForm

    def get_permission_form(self):
        return FakePermissionForm

    def get_lms_permission_form(self):
        return FakeLmsPermissionForm

FORM_CREATOR = FakeFormCreator()

LAB_NAME = 'Laboratory name'
LAB_ID   = 'lab-id'
FAKE_ADDRESS = 'http://fake-address.com/payload='

class RLMS(BaseRLMS):

    def __init__(self, configuration):
        self.configuration = json.loads(configuration)

    def test(self):
        return None

    def get_laboratories(self):
        return [ Laboratory(LAB_NAME, LAB_ID) ]

    def reserve(self, **kwargs):
        obtained_kwargs = self.configuration.copy()
        obtained_kwargs.update(kwargs)
        return FAKE_ADDRESS + json.dumps(obtained_kwargs)

def register_fake():
    register("FakeRLMS", ['1.0'], __name__)

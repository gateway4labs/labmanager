# -*-*- encoding: utf-8 -*-*-
from labmanager.database import db_session as DBS

class SBBase(object):

    @classmethod
    def find(klass, query_id = None, **kwargs):
        query_obj = DBS.query(klass)
        if query_id is not None:
            query_obj = query_obj.filter(klass.id == query_id)
        if kwargs:
            query_obj = query_obj.filter_by(**kwargs)
        return query_obj.first()

    @classmethod
    def all(klass, **kwargs):
        query_obj = DBS.query(klass)
        if kwargs:
            query_obj = query_obj.filter_by(**kwargs)
        return query_obj.all()

    @classmethod
    def new(klass, **params):
        instance = klass(**params)
        DBS.add(instance)
        DBS.commit()
        return instance

from .rlms import RLMS
from .lms import LMS, LMSUser
from .laboratory import Laboratory, PermissionOnLaboratory
from .credential import Credential
from .permission import Permission
from .course import Course
from .user import LabManagerUser

# Avoid pyflakes warnings
assert RLMS
assert LMS
assert LMSUser
assert Laboratory
assert PermissionOnLaboratory
assert Credential
assert Permission
assert Course
assert LabManagerUser


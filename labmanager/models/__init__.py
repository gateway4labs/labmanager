# -*-*- encoding: utf-8 -*-*-
from labmanager.database import db_session as DBS

class SBBase(object):

    @classmethod
    def find(self, query_id = None):
        return DBS.query(self).filter(self.id == query_id).first()

    @classmethod
    def all(args):
        return DBS.query(args).all()

    @classmethod
    def new(self, **params):
        instance = self(**params)
        DBS.add(instance)
        DBS.commit()
        return instance

from .rlms import RLMS
from .lms import NewLMS
from .laboratory import Laboratory, PermissionOnLaboratory
from .credential import Credential
from .permission import Permission
from .course import NewCourse
from .user import LabManagerUser

# Avoid pyflakes warnings
assert RLMS
assert NewLMS
assert Laboratory
assert PermissionOnLaboratory
assert Credential
assert Permission
assert NewCourse
assert LabManagerUser


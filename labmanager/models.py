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

from sqlalchemy import Column, Integer, Unicode, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relation, backref
from labmanager.database import Base, db_session as DBS

class LMS(Base):

    __tablename__ = 'LMSs'

    id = Column(Integer, primary_key=True)

    name                = Column(Unicode(50), nullable = False)
    url                 = Column(Unicode(300), nullable = False) # remote url

    lms_login           = Column(Unicode(50), nullable = False, unique=True)
    lms_password        = Column(Unicode(50), nullable = False) # hash
    
    labmanager_login    = Column(Unicode(50), nullable = False)
    labmanager_password = Column(Unicode(50), nullable = False) # plaintext: my password there

    def __init__(self, name = None, url = None, lms_login = None, lms_password = None, labmanager_login = None, labmanager_password = None):
        self.name                = name
        self.url                 = url
        self.lms_login           = lms_login
        self.lms_password        = lms_password
        self.labmanager_login    = labmanager_login
        self.labmanager_password = labmanager_password


class LabManagerUser(Base):
    __tablename__ = 'LabManagerUsers'

    id = Column(Integer, primary_key=True)

    login    = Column(Unicode(50),  unique = True ) 
    name     = Column(Unicode(50) )
    password = Column(Unicode(50)) # hash

    def __init__(self, login = None, name = None, password = None):
        self.login    = login
        self.name     = name
        self.password = password


class RLMSType(Base):
    __tablename__ = 'RLMS_types'

    id = Column(Integer, primary_key = True)

    name    = Column(Unicode(50), unique = True)

    def __init__(self, name = None):
        self.name = name

    def __repr__(self):
        return 'RLMSType(%r)' % self.name

class RLMSTypeVersion(Base):
    __tablename__  = 'RLMS_type_versions'
    __table_args__ = (UniqueConstraint('rlms_type_id', 'version'), )

    id = Column(Integer, primary_key = True)

    rlms_type_id = Column(Integer, ForeignKey('RLMS_types.id'), nullable = False)
    version = Column(Unicode(50))

    rlms_type = relation(RLMSType.__name__, backref = backref('versions', order_by=id, cascade = 'all,delete'))

    def __init__(self, rlms_type = None, version = None):
        self.rlms_type = rlms_type
        self.version   = version


class RLMS(Base):
    __tablename__ = 'RLMSs'
    
    id = Column(Integer, primary_key = True)

    name     = Column(Unicode(100), nullable = False)
    location = Column(Unicode(100), nullable = False)
    rlms_version_id = Column(Integer, ForeignKey('RLMS_type_versions.id'), nullable = False)

    configuration = Column(Unicode(10 * 1024)) # JSON document
    
    rlms_version = relation(RLMSTypeVersion.__name__, backref = backref('rlms', order_by=id, cascade = 'all,delete'))

    def __init__(self, name = None, location = None, rlms_version = None, configuration = None):
        self.name          = name
        self.location      = location
        self.rlms_version  = rlms_version
        self.configuration = configuration

class Laboratory(Base):
    __tablename__ = 'Laboratories'
    __table_args__ = (UniqueConstraint('laboratory_id', 'rlms_id'), )

    id = Column(Integer, primary_key = True)

    name          = Column(Unicode(50), nullable = False)
    laboratory_id = Column(Unicode(50), nullable = False)
    rlms_id       = Column(Integer, ForeignKey('RLMSs.id'), nullable = False)

    rlms          = relation(RLMS.__name__, backref = backref('laboratories', order_by=id, cascade = 'all,delete'))

    def __init__(self, name = None, laboratory_id = None, rlms = None):
        self.name          = name
        self.laboratory_id = laboratory_id
        self.rlms          = rlms


class PermissionOnLaboratory(Base):
    __tablename__ = 'PermissionOnLaboratories'
    __table_args__ = (UniqueConstraint('laboratory_id', 'lms_id'), UniqueConstraint('local_identifier', 'lms_id'))

    id = Column(Integer, primary_key = True)

    local_identifier     = Column(Unicode(100), nullable = False, index = True)

    laboratory_id = Column(Integer, ForeignKey('Laboratories.id'), nullable = False)
    lms_id        = Column(Integer, ForeignKey('LMSs.id'),  nullable = False)

    configuration = Column(Unicode(10 * 1024)) # JSON document

    laboratory = relation(Laboratory.__name__,  backref = backref('permissions', order_by=id, cascade = 'all,delete'))
    lms        = relation(LMS.__name__, backref = backref('permissions', order_by=id, cascade = 'all,delete'))

    def __init__(self, lms = None, laboratory = None, configuration = None, local_identifier = None):
        self.lms              = lms
        self.laboratory       = laboratory
        self.configuration    = configuration
        self.local_identifier = local_identifier


class Course(Base):
    __tablename__  = 'Courses'
    __table_args__ = (UniqueConstraint('course_id', 'lms_id'), )

    id = Column(Integer, primary_key = True)

    # The ID in the remote LMS
    course_id = Column(Unicode(50), nullable = False)

    name   = Column(Unicode(50), nullable = False)

    lms_id = Column(Integer, ForeignKey('LMSs.id'), nullable = False)

    lms  = relation(LMS.__name__, backref = backref('courses', order_by=id, cascade = 'all,delete'))

    def __init__(self, lms = None, course_id = None, name = None):
        self.course_id = course_id
        self.name      = name
        self.lms       = lms

class PermissionOnCourse(Base):
    __tablename__  = 'PermissionOnCourses'
    __table_args__ = (UniqueConstraint('course_id', 'permission_on_lab_id'),)
    
    id = Column(Integer, primary_key = True)

    configuration        = Column(Unicode(10 * 1024)) # JSON document

    permission_on_lab_id = Column(Integer, ForeignKey('PermissionOnLaboratories.id'), nullable = False)
    course_id            = Column(Integer, ForeignKey('Courses.id'), nullable = False)

    permission_on_lab    = relation(PermissionOnLaboratory.__name__, backref = backref('course_permissions', order_by=id, cascade = 'all,delete'))
    course               = relation(Course.__name__, backref = backref('permissions', order_by=id, cascade = 'all,delete'))

    def __init__(self, permission_on_lab = None, course = None, configuration = None):
        self.permission_on_lab = permission_on_lab
        self.course            = course
        self.configuration     = configuration

class SBBase(object):

    @classmethod
    def find(self, query_id = None):
        return find_by_id(self, query_id)

    @classmethod
    def all(args):
        return find_all(args)

def find_by_id(self, query_id):
    return DBS.query(self).filter(self.id == query_id).first()

def find_all(self):
    return DBS.query(self).all()


class NewLMS(Base, SBBase):
    __tablename__  = 'newlmss'
    id = Column(Integer, primary_key = True)
    name = Column(Unicode(50), nullable = False)
    url = Column(Unicode(300), nullable = False)

    permissions_on_experiments = relation('Permission', backref=backref('newlms', order_by=id))
    authentications = relation('Credential', backref=backref('newlms', order_by=id))
    courses = relation('NewCourse', backref=backref('newlms', order_by=id))

    def __init__(self, name = None, url = None):
        self.name = name
        self.url = url

    def __repr__(self):
        return "<NewLMS:%s %s>" % (self.id, self.name)

    def __unicode__(self):
        return self.name

class Credential(Base):
    __tablename__  = 'credentials'
    id = Column(Integer, primary_key = True)
    key = Column(Unicode(50), nullable = False, unique=True)
    kind = Column(Unicode(50), nullable = False)
    lms_id = Column(Integer, ForeignKey('newlmss.id'), nullable = False)
    secret = Column(Unicode(50), nullable = False)

    def __init__(self, key = None, secret = None, type = None):
        self.key = key
        self.secret = secret
        self.type = type

    def __repr__(self):
        return "<Credential: %s LMS:%s>" % (self.lms_id, self.kind)

class Permission(Base, SBBase):
    __tablename__  = 'permissions'
    id = Column(Integer, primary_key = True)
    access = Column(Unicode(50), nullable = False)
    context_id = Column(Unicode(50), nullable = False)
    experiment_id = Column(Integer, ForeignKey('experiments.id'), nullable = False)
    lms_id = Column(Integer, ForeignKey('newlmss.id'), nullable = False)
    resource_link_id = Column(Integer, nullable = False)
    configuration = Column(Unicode(10 * 1024), nullable = True)

    def __init__(self, lms = None, context_id = None, resource_link_id = None,
                 experiment = None, access = None):
        self.newlms = lms
        self.context_id = context_id
        self.resource_link_id = resource_link_id
        self.experiment = experiment
        self.access = access

    def __repr__(self):
        return "<Permission %d: %s LMS:%s %s>" % (self.id, self.experiment_id, self.lms_id, self.access)

    def __unicode__(self):
        return "Permission %d: %s from %s on %s" % (self.id, self.access, self.lms_id, self.experiment_id)

    def change_status(self, new_status):
        self.access = new_status
        DBS.commit()

    @classmethod
    def find_by_status(self, status):
        return DBS.query(self).filter(self.access == status).all()

class Experiment(Base):
    __tablename__  = 'experiments'
    id = Column(Integer, primary_key = True)
    name = Column(Unicode(50), nullable = False)
    rlms_id = Column(Integer, ForeignKey('newrlmss.id'), nullable = False)
    url = Column(Unicode(300), nullable = False)

    permissions = relation('Permission', backref=backref('experiment',order_by=id))

    def __init__(self, name = None, rlms = None, url = None):
        self.name = name
        self.newrlms = rlms
        self.url = url

    def __repr__(self):
        return "<Experiment: %s version:%s>" % (self.name, self.newrlms)

    def __unicode__(self):
        return "%s @ %s" % (self.name, self.newrlms)


class NewCourse(Base):
    __tablename__ = 'newcourses'
    id = Column(Integer, primary_key = True)
    lms_id = Column(Integer, ForeignKey('newlmss.id'), nullable = False)
    name = Column(Unicode(50), nullable = False)

    def __init__(self, name = None):
        self.name = name

    def __repr__(self):
        return "<NewCourse: %s LMS:%s>" % (self.name, self.lms_id)

    def __unicode__(self):
        return "%s on %s" % (self.name, self.lms_id)


class NewRLMS(Base):
    __tablename__ = 'newrlmss'
    id = Column(Integer, primary_key = True)
    kind = Column(Unicode(50), nullable = False)
    location = Column(Unicode(50), nullable = False)
    url = Column(Unicode(300), nullable = False)
    version = Column(Unicode(50), nullable = False)

    experiments = relation('Experiment', backref=backref('newrlms', order_by=id))

    def __init__(self, kind = None, url = None, location = None, version = None):
        self.kind = kind
        self.location = location
        self.url = url
        self.version = version

    def __repr__(self):
        return "<NewRLMS: %s %s %s>" % (self.kind, self.version, self.location)

    def __unicode__(self):
        return "%s on %s" % (self.kind, self.location)


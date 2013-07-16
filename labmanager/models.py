# -*-*- encoding: utf-8 -*-*-

import hashlib

from sqlalchemy import Column, Integer, Unicode, ForeignKey, UniqueConstraint, sql, Table, Boolean
from sqlalchemy.orm import relation, backref, relationship

from flask.ext.login import UserMixin

from labmanager.db import Base, db_session as DBS

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


######################################################################################
# 
#              B A S I C   C O N C E P T S
# 
#   + RLMS  
#     - Laboratory
# 
#   + LMS
#     - Course
#     - LmsUser
#     - BasicHttpCredentials
#
#   + LabManagerUser
# 


#########################################################
# 
#     LabManager Users
#    
#   Typically administrators. They log in and they can
#   add RLMSs, LMSs, etc.
# 

class LabManagerUser(Base, SBBase, UserMixin):
    __tablename__ = 'LabManagerUsers'

    id = Column(Integer, primary_key=True)

    login    = Column(Unicode(50), unique = True )
    name     = Column(Unicode(50), nullable = False)
    password = Column(Unicode(50), nullable = False) # hash

    def __init__(self, login = None, name = None, password = None):
        self.login    = login
        self.name     = name
        self.password = password

    def __repr__(self):
        return "LabMUser(%r, %r, %r, %r)" % (self.login, self.name, self.password)

    def __unicode__(self):
        return self.name

    def get_id(self):
        return u'labmanager_admin::%s' % self.login

    @classmethod
    def exists(self, login, word):
        return DBS.query(self).filter(sql.and_(self.login == login, self.password == word)).first()


#########################################################
# 
#     RLMS: Remote Laboratory Management System   
#    
#   1 RLMS is composed of 1 or multiple Laboratories
# 


class RLMS(Base, SBBase):
    __tablename__ = 'rlmss'
    id = Column(Integer, primary_key = True)
    kind = Column(Unicode(50), nullable = False)
    location = Column(Unicode(50), nullable = False)
    url = Column(Unicode(300), nullable = False)
    version = Column(Unicode(50), nullable = False)

    configuration = Column(Unicode(10 * 1024))

    def __init__(self, kind = None, url = None, location = None, version = None, configuration = '{}'):
        self.kind = kind
        self.location = location
        self.url = url
        self.version = version
        self.configuration = configuration

    def __repr__(self):
        return "RLMS(kind = %r, url=%r, location=%r, version=%r, configuration=%r)" % (self.kind, self.url, self.location, self.version, self.configuration)

    def __unicode__(self):
        return u"%s on %s" % (self.kind, self.location)


#######################################################################
# 
#     Laboratory
# 
#  1 Laboratory is the minimum representation that can be reserved.
# 


class Laboratory(Base, SBBase):
    __tablename__ = 'laboratories'
    __table_args__ = (UniqueConstraint('laboratory_id', 'rlms_id'), )

    id = Column(Integer, primary_key = True)

    name          = Column(Unicode(50), nullable = False)
    laboratory_id = Column(Unicode(50), nullable = False)
    rlms_id       = Column(Integer, ForeignKey('rlmss.id'), nullable = False)
    visibility    = Column(Unicode(50), nullable = False, index = True, default = u'private')
    available     = Column(Boolean, nullable = False, index = True, default = False)

    rlms          = relation(RLMS.__name__, backref = backref('laboratories', order_by=id, cascade = 'all,delete'))

    def __init__(self, name = None, laboratory_id = None, rlms = None, visibility = None, available = None):
        self.name          = name
        self.laboratory_id = laboratory_id
        self.rlms          = rlms
        self.visibility    = visibility
        self.available     = available

    def __unicode__(self):
        return u'%s at %s' % (self.name, self.rlms)


#######################################################################
# 
#     LMS
# 
# 1 LMS (or CMS or PLE) is a system that manages authentication and
# authorization. It is divided into multiple courses (see below).
# 


class LMS(Base, SBBase):

    __tablename__  = 'lmss'
    __table_args__ = (UniqueConstraint('name'), UniqueConstraint('full_name'))

    id = Column(Integer, primary_key = True)
    name      = Column(Unicode(50), nullable = False, index = True)
    full_name = Column(Unicode(50), nullable = False, index = True)
    url       = Column(Unicode(300), nullable = False)

    def __init__(self, name = None, full_name = None, url = None):
        self.name = name
        self.full_name = full_name
        self.url = url

    def __repr__(self):
        return "LMS(%r, %r, %r)" % (self.name, self.full_name, self.url)

    def __unicode__(self):
        return self.name


##################################################
# 
#         LMS Basic HTTP Credentials
# 
#   Used by LMSs to authenticate in the system
# 

class BasicHttpCredentials(Base, SBBase):

    __tablename__  = 'basic_http_credentials'
    __table_args__ = (UniqueConstraint('lms_login'), UniqueConstraint('lms_id'))

    id        = Column(Integer, primary_key = True)
    lms_id        = Column(Integer, ForeignKey('lmss.id'), nullable = False)

    # Arguments for the LMS to connect the LabManager
    lms_login     = Column(Unicode(50), nullable = False)
    lms_password  = Column(Unicode(50), nullable = False)

    # Arguments for the LabManager to connect the LMS. Might be null
    lms_url       = Column(Unicode(300), nullable = True)
    labmanager_login    = Column(Unicode(50), nullable = True)
    labmanager_password = Column(Unicode(50), nullable = True)

    lms = relation('LMS', backref=backref('basic_http_authentications', order_by=id, cascade='all, delete'))

    def __init__(self, lms_login = None, lms_password = None, lms = None, lms_url = None, labmanager_login = None, labmanager_password = None):
        self.lms                 = lms
        self.lms_login           = lms_login
        self.lms_password        = lms_password
        self.lms_url             = lms_url
        self.labmanager_login    = labmanager_login
        self.labmanager_password = labmanager_password


    def __repr__(self):
        return "BasicHttpCredentials(lms_login=%r, lms_password=%r, lms=%r, lms_url=%r, labmanager_login=%r, labmanager_password=%r)" % ( self.lms_login, self.password, self.lms, self.lms_url, self.labmanager_login, self.labmanager_password)

    def __unicode__(self):
        return "Basic HTTP auth for %s" %(self.lms.name)

    def update_password(self, old_password):
        if self.lms_password != old_password:
            self.lms_password = hashlib.new('sha', self.lms_password).hexdigest()

##################################################
# 
#         LMS Basic HTTP Credentials
# 
#   Used by LMSs to authenticate in the system
# 

class ShindigCredentials(Base, SBBase):

    __tablename__  = 'shindig_credentials'
    __table_args__ = (UniqueConstraint('lms_id'),)

    id        = Column(Integer, primary_key = True)
    lms_id        = Column(Integer, ForeignKey('lmss.id'), nullable = False)

    # The URL of the Shindig server. Example: http://shindig.epfl.ch (no trailing slash)
    shindig_url   = Column(Unicode(50), nullable = False)

    lms = relation('LMS', backref=backref('shindig_credentials', order_by=id, cascade='all, delete'))

    def __init__(self, lms = None, shindig_url = None):
        self.lms         = lms
        self.shindig_url = shindig_url


    def __repr__(self):
        return "ShindigCredentials(lms=%r, shindig_url=%r)" % ( self.lms, self.shindig_url )

    def __unicode__(self):
        return "ShindigCredentials for %s" % (self.lms.name)


##################################################
# 
#                   LMS User
# 
#   LMS Users (administrators or teachers) can
#   authenticate and change stuff at LMS level.
#  

users2courses_relation = Table('users2courses', Base.metadata,
    Column('course_id',   Integer, ForeignKey('courses.id')),
    Column('lms_user_id', Integer, ForeignKey('lmsusers.id'))
)

class LmsUser(Base, SBBase, UserMixin):
    __tablename__  = 'lmsusers'
    __table_args__ = (UniqueConstraint('login','lms_id'), )

    id           = Column(Integer, primary_key = True)

    login        = Column(Unicode(50), nullable = False, index = True)
    full_name    = Column(Unicode(50), nullable = False)
    password     = Column(Unicode(128), nullable = False)
    access_level = Column(Unicode(50), nullable = False)

    lms_id    = Column(Integer, ForeignKey('lmss.id'), nullable = False)

    lms       = relation('LMS', backref = backref('users', order_by=id, cascade = 'all,delete'))

    courses = relationship("Course",
                    secondary=users2courses_relation,
                    backref="users")

    def __init__(self, login = None, full_name = None, lms = None, access_level = None):
        self.login        = login
        self.full_name    = full_name
        self.lms          = lms
        self.access_level = access_level

    def __unicode__(self):
        return u'%s@%s' % (self.login, self.lms.name)
    
    def get_id(self):
        return u'lms_user::%s::%s' % (self.lms.name, self.login)

    @classmethod
    def exists(self, login, word, lms_id):
        return DBS.query(self).filter_by(login = login, password = word, lms_id = int(lms_id)).first()    




#####################################################################################
# 
#    Course
# 
#  1 Course is part of a LMS and it will have permission on certain laboratories
# 

class Course(Base, SBBase):

    __tablename__ = 'courses'
    __table_args__ = (UniqueConstraint('lms_id','context_id'), )

    id = Column(Integer, primary_key = True)

    lms_id = Column(Integer, ForeignKey('lmss.id'), nullable = False)
    name = Column(Unicode(50), nullable = False)
    context_id = Column(Unicode(50), nullable = False)

    lms = relation('LMS', backref=backref('courses', order_by=id, cascade='all, delete'))

    def __init__(self, name = None, lms = None, context_id = None):
        self.name = name
        self.lms = lms
        self.context_id = context_id

    def __repr__(self):
        return "Course(name=%r, lms=%r, context_id=%r)" % (self.name, self.lms, self.context_id)

    def __unicode__(self):
        return "%s on %s" % (self.name, self.lms)


######################################################################################
# 
#              P E R M I S S I O N S 
# 
#   - Permission on LMS (=> LMS)
#     + Permission on LMS User (may or may not exist)
#       + Permission on Course
# 

########################################################
# 
#     PermissionToLms
#
# Defines that a LMS has permission on a Laboratory.
#

class PermissionToLms(Base, SBBase):
    __tablename__ = 'PermissionToLmss'
    __table_args__ = (UniqueConstraint('laboratory_id', 'lms_id'), UniqueConstraint('local_identifier', 'lms_id'))

    id = Column(Integer, primary_key = True)

    local_identifier     = Column(Unicode(100), nullable = False, index = True)

    laboratory_id = Column(Integer, ForeignKey('laboratories.id'), nullable = False)
    lms_id        = Column(Integer, ForeignKey('lmss.id'),  nullable = False)

    configuration = Column(Unicode(10 * 1024)) # JSON document
    accessible    = Column(Boolean, nullable = False, index = True, default = False)

    laboratory = relation(Laboratory.__name__,  backref = backref('lab_permissions', order_by=id, cascade = 'all,delete'))
    lms        = relation(LMS.__name__, backref = backref('lab_permissions', order_by=id, cascade = 'all,delete'))

    def __init__(self, lms = None, laboratory = None, configuration = None, local_identifier = None, accessible = None):
        self.lms              = lms
        self.laboratory       = laboratory
        self.configuration    = configuration
        self.local_identifier = local_identifier
        self.accessible       = accessible

    def __unicode__(self):
        return u"'%s': lab %s to %s" % (self.local_identifier, self.laboratory.name, self.lms.name)


########################################################
# 
#     PermissionToLmsUser
#
# Defines that a LMS User has permission on a Laboratory.
#

class PermissionToLmsUser(Base, SBBase):

    __tablename__  = 'PermissionsToLmsUsers'
    __table_args__ = (UniqueConstraint('permission_to_lms_id', 'lms_user_id'),)

    id = Column(Integer, primary_key = True)

    permission_to_lms_id = Column(Integer, ForeignKey('PermissionToLmss.id'), nullable = False, index = True)
    lms_user_id          = Column(Integer, ForeignKey('lmsusers.id'), nullable = False, index = True)
    
    # LTI data
    key                  = Column(Unicode(100), nullable = False, unique = True)
    secret               = Column(Unicode(100), nullable = False)

    permission_to_lms = relation('PermissionToLms', backref=backref('lms_user_permissions', order_by=id, cascade='all, delete'))
    lms_user = relation('LmsUser', backref=backref('lms_user_permissions', order_by=id, cascade='all, delete'))

    def __init__(self, permission_to_lms = None, lms_user = None, key = None, secret = None):
        self.permission_to_lms = permission_to_lms
        self.lms_user          = lms_user
        self.key               = key
        self.secret            = secret


########################################################
# 
#     Permission To Course
#
# Defines that a Course has permission on a Laboratory.
#


class PermissionToCourse(Base, SBBase):

    __tablename__  = 'PermissionsToCourses'
    __table_args__ = (UniqueConstraint('permission_to_lms_id', 'course_id'),)

    id = Column(Integer, primary_key = True)

    configuration = Column(Unicode(10 * 1024), nullable = True)

    permission_to_lms_id = Column(Integer, ForeignKey('PermissionToLmss.id'), nullable = False)
    course_id            = Column(Integer, ForeignKey('courses.id'), nullable = False)


    permission_to_lms = relation('PermissionToLms', backref=backref('course_permissions', order_by=id, cascade='all, delete'))
    course            = relation('Course', backref=backref('permissions', order_by=id, cascade='all, delete'))

    def __init__(self, course = None, permission_to_lms = None,
                 configuration = None):
        self.course            = course
        self.configuration     = configuration
        self.permission_to_lms = permission_to_lms

    def __repr__(self):
        return "PermissionToCourse(course=%r, configuration=%r, permission_to_lms=%r)" % (self.course, self.configuration, self.permission_to_lms)

    def __unicode__(self):
        return u"%s from %s on %s" % (self.course.name,
                                           self.course.lms.name,
                                           self.permission_to_lms)



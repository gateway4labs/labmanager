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
#   + LearningTool
#     - Course
#     - LtUser
#     - BasicHttpCredentials
#
#   + LabManagerUser
# 


#########################################################
# 
#     LabManager Users
#    
#   Typically administrators. They log in and they can
#   add RLMSs, LTs, etc.
# 

class LabManagerUser(Base, SBBase, UserMixin):
    __tablename__ = 'labmanager_users'

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


    # validated: true or false. True means that the last time that the validation process took place it was a success. The validation process involves that the labmanager admin checks the correctness of the credentials provided during the RLMS creation. False means that the last time that the validation took place, it did not succeed.


    # completed: true or false. This is, if all the steps in the creation of the RLMS have already been taken, then completed=true. At present, completed can only be false for HTTP RLMSs (because the creation process takes more than one step, as opposed to Weblab...)


    validated = Column(Boolean, default = False)

    completed = Column(Boolean, default = True)

    configuration = Column(Unicode(10 * 1024))

    def __init__(self, kind = None, url = None, location = None, version = None, configuration = '{}'):
        self.kind = "saaskind" # kind
        self.location = "saasloc" # location
        self.url = "saasurl" # url
        self.version = "saasver" # version
        self.configuration = configuration

        self.validated = False

        
#        if kind is "HTTP": 
#            self.completed  = Falseththt
#        else: 
#            self.completed  = Truethth  

#        
#        raise Exception(self.url)
#        if "HTTP"  in kind:
#            self.completed  = Falseththt
#            
#        else: 
#                    
##            raise Exception("http not in kind %s", kind )
#            self.completed  = Truethth 
#               



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

    name                     = Column(Unicode(50), nullable = False)
    laboratory_id            = Column(Unicode(50), nullable = False)
    rlms_id                  = Column(Integer, ForeignKey('rlmss.id'), nullable = False)
    visibility               = Column(Unicode(50), nullable = False, index = True, default = u'private')
    available                = Column(Boolean, nullable = False, index = True, default = False)
    default_local_identifier = Column(Unicode(50), nullable = False, default = u"")

    publicly_available       = Column(Boolean, nullable = False, index = True, default = False)
    public_identifier        = Column(Unicode(50), nullable = False, default = u"")

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
#     LearningTool
# 
# 1 LearningTool (or CMS or PLE) is a system that manages authentication and
# authorization. It is divided into multiple courses (see below).
# 


class LearningTool(Base, SBBase):

    __tablename__  = 'learning_tools'
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
        return "LearningTool(%r, %r, %r)" % (self.name, self.full_name, self.url)

    def __unicode__(self):
        return self.name


##################################################
# 
#         LT Basic HTTP Credentials
# 
#   Used by LTs to authenticate in the system
# 

class BasicHttpCredentials(Base, SBBase):

    __tablename__  = 'basic_http_credentials'
    __table_args__ = (UniqueConstraint('lt_login'), UniqueConstraint('lt_id'))

    id        = Column(Integer, primary_key = True)
    lt_id        = Column(Integer, ForeignKey('learning_tools.id'), nullable = False)

    # Arguments for the LT to connect the LabManager
    lt_login     = Column(Unicode(50), nullable = False)
    lt_password  = Column(Unicode(50), nullable = False)

    # Arguments for the LabManager to connect the LT. Might be null
    lt_url       = Column(Unicode(300), nullable = True)
    labmanager_login    = Column(Unicode(50), nullable = True)
    labmanager_password = Column(Unicode(50), nullable = True)

    lt = relation('LearningTool', backref=backref('basic_http_authentications', order_by=id, cascade='all, delete'))

    def __init__(self, lt_login = None, lt_password = None, lt = None, lt_url = None, labmanager_login = None, labmanager_password = None):
        self.lt                  = lt
        self.lt_login            = lt_login
        self.lt_password         = lt_password
        self.lt_url              = lt_url
        self.labmanager_login    = labmanager_login
        self.labmanager_password = labmanager_password


    def __repr__(self):
        return "BasicHttpCredentials(lt_login=%r, lt_password=%r, lt=%r, lt_url=%r, labmanager_login=%r, labmanager_password=%r)" % ( self.lt_login, self.password, self.lt, self.lt_url, self.labmanager_login, self.labmanager_password)

    def __unicode__(self):
        return "Basic HTTP auth for %s" %(self.lt.name)

    def update_password(self, old_password):
        if self.lt_password != old_password:
            self.lt_password = hashlib.new('sha', self.lt_password).hexdigest()

##################################################
# 
#         LT Shindig credentials
# 
#   Used by LTs to authenticate in the system
# 

class ShindigCredentials(Base, SBBase):

    __tablename__  = 'shindig_credentials'
    __table_args__ = (UniqueConstraint('lt_id'),)

    id        = Column(Integer, primary_key = True)
    lt_id        = Column(Integer, ForeignKey('learning_tools.id'), nullable = False)

    # The URL of the Shindig server. Example: http://shindig.epfl.ch (no trailing slash)
    shindig_url   = Column(Unicode(50), nullable = False)

    lt = relation('LearningTool', backref=backref('shindig_credentials', order_by=id, cascade='all, delete'))

    def __init__(self, lt = None, shindig_url = None):
        self.lt         = lt
        self.shindig_url = shindig_url


    def __repr__(self):
        return "ShindigCredentials(lt=%r, shindig_url=%r)" % ( self.lt, self.shindig_url )

    def __unicode__(self):
        return "ShindigCredentials for %s" % (self.lt.name)


##################################################
# 
#                   LT User
# 
#   LT Users (administrators or teachers) can
#   authenticate and change stuff at LT level.
#  

users2courses_relation = Table('users2courses', Base.metadata,
    Column('course_id',   Integer, ForeignKey('courses.id')),
    Column('lt_user_id', Integer, ForeignKey('lt_users.id'))
)

class LtUser(Base, SBBase, UserMixin):
    __tablename__  = 'lt_users'
    __table_args__ = (UniqueConstraint('login','lt_id'), )

    id           = Column(Integer, primary_key = True)

    login        = Column(Unicode(50), nullable = False, index = True)
    full_name    = Column(Unicode(50), nullable = False)
    password     = Column(Unicode(128), nullable = False)
    access_level = Column(Unicode(50), nullable = False)

    lt_id    = Column(Integer, ForeignKey('learning_tools.id'), nullable = False)

    lt       = relation('LearningTool', backref = backref('users', order_by=id, cascade = 'all,delete'))

    courses = relationship("Course",
                    secondary=users2courses_relation,
                    backref="users")

    def __init__(self, login = None, full_name = None, lt = None, access_level = None):
        self.login        = login
        self.full_name    = full_name
        self.lt           = lt
        self.access_level = access_level

    def __unicode__(self):
        return u'%s@%s' % (self.login, self.lt.name)
    
    def get_id(self):
        return u'lt_user::%s::%s' % (self.lt.name, self.login)

    @classmethod
    def exists(self, login, word, lt_id):
        return DBS.query(self).filter_by(login = login, password = word, lt_id = int(lt_id)).first()    




#####################################################################################
# 
#    Course
# 
#  1 Course is part of a LT and it will have permission on certain laboratories
# 

class Course(Base, SBBase):

    __tablename__ = 'courses'
    __table_args__ = (UniqueConstraint('lt_id','context_id'), )

    id = Column(Integer, primary_key = True)

    lt_id = Column(Integer, ForeignKey('learning_tools.id'), nullable = False)
    name = Column(Unicode(50), nullable = False)
    context_id = Column(Unicode(50), nullable = False)

    lt = relation('LearningTool', backref=backref('courses', order_by=id, cascade='all, delete'))

    def __init__(self, name = None, lt = None, context_id = None):
        self.name = name
        self.lt   = lt
        self.context_id = context_id

    def __repr__(self):
        return "Course(name=%r, lt=%r, context_id=%r)" % (self.name, self.lt, self.context_id)

    def __unicode__(self):
        return "%s on %s" % (self.name, self.lt)


######################################################################################
# 
#              P E R M I S S I O N S 
# 
#   - Permission on LT (=> LT)
#     + Permission on LT User (may or may not exist)
#       + Permission on Course
#
#   - RequestPermissionLT
#       When a school requests permission to use a lab, and the labmanager admin must grant or reject this request.
#       If the request is granted, a new entry is created in PermissionToLt

########################################################
# 
#     PermissionToLt
#
# Defines that a LT has permission on a Laboratory.
#

class PermissionToLt(Base, SBBase):
    __tablename__ = 'permissions2lt'
    __table_args__ = (UniqueConstraint('laboratory_id', 'lt_id'), UniqueConstraint('local_identifier', 'lt_id'))

    id = Column(Integer, primary_key = True)

    local_identifier     = Column(Unicode(100), nullable = False, index = True)

    laboratory_id = Column(Integer, ForeignKey('laboratories.id'), nullable = False)
    lt_id        = Column(Integer, ForeignKey('learning_tools.id'),  nullable = False)

    configuration = Column(Unicode(10 * 1024)) # JSON document
    accessible    = Column(Boolean, nullable = False, index = True, default = False)

    laboratory = relation(Laboratory.__name__,  backref = backref('lab_permissions', order_by=id, cascade = 'all,delete'))
    lt        = relation(LearningTool.__name__, backref = backref('lab_permissions', order_by=id, cascade = 'all,delete'))

    def __init__(self, lt = None, laboratory = None, configuration = None, local_identifier = None, accessible = None):
        self.lt               = lt
        self.laboratory       = laboratory
        self.configuration    = configuration
        self.local_identifier = local_identifier
        self.accessible       = accessible

    def __unicode__(self):
        return u"'%s': lab %s to %s" % (self.local_identifier, self.laboratory.name, self.lt.name)




########################################################
# 
#     PermissionToLtUser
#
# Defines that a LT User has permission on a Laboratory.
#

class PermissionToLtUser(Base, SBBase):

    __tablename__  = 'permissions2ltuser'
    __table_args__ = (UniqueConstraint('permission_to_lt_id', 'lt_user_id'),)

    id = Column(Integer, primary_key = True)

    permission_to_lt_id = Column(Integer, ForeignKey('permissions2lt.id'), nullable = False, index = True)
    lt_user_id          = Column(Integer, ForeignKey('lt_users.id'), nullable = False, index = True)
    
    # LTI data
    key                  = Column(Unicode(100), nullable = False, unique = True)
    secret               = Column(Unicode(100), nullable = False)

    permission_to_lt = relation('PermissionToLt', backref=backref('lt_user_permissions', order_by=id, cascade='all, delete'))
    lt_user = relation('LtUser', backref=backref('lt_user_permissions', order_by=id, cascade='all, delete'))

    def __init__(self, permission_to_lt = None, lt_user = None, key = None, secret = None):
        self.permission_to_lt = permission_to_lt
        self.lt_user          = lt_user
        self.key               = key
        self.secret            = secret


########################################################
# 
#     Permission To Course
#
# Defines that a Course has permission on a Laboratory.
#


class PermissionToCourse(Base, SBBase):

    __tablename__  = 'permissions2course'
    __table_args__ = (UniqueConstraint('permission_to_lt_id', 'course_id'),)

    id = Column(Integer, primary_key = True)

    configuration = Column(Unicode(10 * 1024), nullable = True)

    permission_to_lt_id = Column(Integer, ForeignKey('permissions2lt.id'), nullable = False)
    course_id            = Column(Integer, ForeignKey('courses.id'), nullable = False)


    permission_to_lt = relation('PermissionToLt', backref=backref('course_permissions', order_by=id, cascade='all, delete'))
    course            = relation('Course', backref=backref('permissions', order_by=id, cascade='all, delete'))

    def __init__(self, course = None, permission_to_lt = None,
                 configuration = None):
        self.course            = course
        self.configuration     = configuration
        self.permission_to_lt = permission_to_lt

    def __repr__(self):
        return "PermissionToCourse(course=%r, configuration=%r, permission_to_lt=%r)" % (self.course, self.configuration, self.permission_to_lt)

    def __unicode__(self):
        return u"%s from %s on %s" % (self.course.name,
                                           self.course.lt.name,
                                           self.permission_to_lt)

########################################################
# 
#     RequestPermissionLT
#
#     When a school requests permission to use a lab, and the labmanager admin must grant or reject this request.
#     If the request is granted, a new entry is created in PermissionToLt


class RequestPermissionLT(Base, SBBase):
    __tablename__ = 'request_permissions_lt'
    __table_args__ = (UniqueConstraint('laboratory_id', 'lt_id'), UniqueConstraint('local_identifier', 'lt_id'))

    id = Column(Integer, primary_key = True)

    local_identifier     = Column(Unicode(100), nullable = False, index = True)

    laboratory_id = Column(Integer, ForeignKey('laboratories.id'), nullable = False)
    lt_id        = Column(Integer, ForeignKey('learning_tools.id'),  nullable = False)

    configuration = Column(Unicode(10 * 1024)) # JSON document
    accessible    = Column(Boolean, nullable = False, index = True, default = False)

    laboratory = relation(Laboratory.__name__,  backref = backref('lab_requestpermissions', order_by=id, cascade = 'all,delete'))
    lt        = relation(LearningTool.__name__, backref = backref('lab_requestpermissions', order_by=id, cascade = 'all,delete'))

    def __init__(self, lt = None, laboratory = None, configuration = None, local_identifier = None, accessible = None):
        self.lt              = lt
        self.laboratory       = laboratory
        self.configuration    = configuration
        self.local_identifier = local_identifier
        self.accessible       = accessible

    def __unicode__(self):
        return u"'%s': lab %s to %s" % (self.local_identifier, self.laboratory.name, self.lt.name)





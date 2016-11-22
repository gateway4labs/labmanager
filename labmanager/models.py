# -*-*- encoding: utf-8 -*-*-

import json
import hashlib
import datetime
import uuid
from sqlalchemy import sql, ForeignKey
from sqlalchemy.orm import relation, backref, relationship
from flask.ext.login import UserMixin
from labmanager.db import db
from labmanager.babel import gettext


TABLE_KWARGS = {
    'mysql_engine' : 'InnoDB',
    # Complete me
}

class SBBase(object):
    @classmethod
    def find(klass, query_id = None, **kwargs):
        query_obj = db.session.query(klass)
        if query_id is not None:
            query_obj = query_obj.filter(klass.id == query_id)
        if kwargs:
            query_obj = query_obj.filter_by(**kwargs)
        return query_obj.first()

    @classmethod
    def all(klass, **kwargs):
        query_obj = db.session.query(klass)
        if kwargs:
            query_obj = query_obj.filter_by(**kwargs)
        return query_obj.all()

    @classmethod
    def new(klass, **params):
        instance = klass(**params)
        db.session.add(instance)
        db.session.commit()
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

class LabManagerUser(db.Model, SBBase, UserMixin):
    __tablename__ = 'labmanager_users'
    __table_args__ = (TABLE_KWARGS)

    id = db.Column(db.Integer, primary_key=True)
    login    = db.Column(db.Unicode(50), unique = True, nullable = False)
    name     = db.Column(db.Unicode(50), nullable = False)
    password = db.Column(db.Unicode(50), nullable = False) # hash

    def __init__(self, login = None, name = None, password = None):
        self.login    = login
        self.name     = name
        self.password = password

    def __repr__(self):
        return "LabManagerUser(%(userlogin)r, %(username)r, %(userpassword)r)" % dict(userlogin=self.login, username=self.name, userpassword=self.password)

    def __unicode__(self):
        return self.name

    def get_id(self):
        return u"labmanager_admin::%s" % self.login

    @classmethod
    def exists(self, login, word):
        return db.session.query(self).filter(sql.and_(self.login == login, self.password == word)).first()

class SiWaySAMLUser(db.Model):
    __tablename__ = 'siway_user'

    # Here the fields that we retrieve at SiWay
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.Unicode(255), index = True, nullable = False, unique = True)
    uid = db.Column(db.Integer,nullable=False)
    employee_type = db.Column(db.Unicode(255),nullable=False)
    full_name = db.Column(db.Unicode(255), nullable = False)
    short_name = db.Column(db.Unicode(255),nullable=False)
    school_name = db.Column(db.Unicode(255), nullable=False)
    group = db.Column(db.Unicode(255), nullable=False)

    def __init__(self, email, uid, employee_type, full_name, short_name, school_name, group):
        self.email = email
        self.uid = uid
        self.employee_type = employee_type
        self.full_name = full_name
        self.short_name = short_name
        self.school_name = school_name
        self.group = group

    def __repr__(self):
        return "SiWaySAMLUsers(%r, %r)" % (self.email, self.short_name)

    def __unicode__(self):
        return u"%s <%s>" % (self.short_name, self.email)




#########################################################
# 
#     RLMS: Remote Laboratory Management System   
#    
#   1 RLMS is composed of 1 or multiple Laboratories
# 

class RLMS(db.Model, SBBase):
    __tablename__ = 'rlmss'
    __table_args__ = (TABLE_KWARGS)

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.Unicode(255))
    kind = db.Column(db.Unicode(50), nullable = False)
    location = db.Column(db.Unicode(255), nullable = False)
    url = db.Column(db.Unicode(300), nullable = False)
    version = db.Column(db.Unicode(50), nullable = False)
    configuration = db.Column(db.Unicode(10 * 1024))

    publicly_available = db.Column(db.Boolean, nullable = False, index = True, default = False)
    # Not unique (otherwise there couldn't be two empty names)
    public_identifier  = db.Column(db.Unicode(50), nullable = False, default = u'')

    default_autoload = db.Column(db.Boolean, nullable = True, index = True, default = None)

    def __init__(self, kind = None, url = None, name = None, location = None, version = None, configuration = '{}', publicly_available = False, public_identifier = u'', default_autoload = None):
        self.kind = kind
        self.location = location
        self.name = name
        self.url = url
        self.version = version
        self.configuration = configuration
        self.publicly_available = publicly_available
        self.public_identifier = public_identifier
        self.default_autoload = default_autoload

    def get_rlms(self):
        rlms_class = get_manager_class(self.kind, self.version, self.id)
        return rlms_class(self.configuration)

    def __repr__(self):
        return "RLMS(kind = %(rlmskind)r, url=%(rlmsurl)r, location=%(rlmslocation)r, version=%(rlmsversion)r, configuration=%(rlmsconfiguration)r, publicly_available=%(publicly_available)r, public_identifier = %(public_identifier)r, default_autoload = %(default_autoload)r)" % dict(rlmskind=self.kind, rlmsurl=self.url, rlmslocation=self.location, rlmsversion=self.version, rlmsconfiguration=self.configuration, publicly_available = self.publicly_available, public_identifier = self.public_identifier, default_autoload = self.default_autoload)

    def get_name(self):
        if self.name:
            return self.name

        return self.kind

    def __unicode__(self):
        return gettext(u"%(kind)s on %(location)s", kind=self.kind, location=self.location)

class RLMSTypeCache(db.Model):
    __tablename__ = 'rlmstype_cache'
    
    id = db.Column(db.Integer, primary_key = True)

    rlms_type = db.Column(db.Unicode(255), nullable = False, index = True)
    key = db.Column(db.Unicode(255), index = True)
    value = db.Column(db.UnicodeText(512 * 1024 * 1024)) # 512 MB
    datetime = db.Column(db.DateTime, index = True)

    def __init__(self, rlms_type, key, value, datetime):
        self.rlms_type = rlms_type
        self.key = key
        self.value = value
        self.datetime = datetime

class RLMSCache(db.Model):
    __tablename__ = 'rlms_caches'
    
    id = db.Column(db.Integer, primary_key = True)

    rlms_id = db.Column(db.Integer, db.ForeignKey('rlmss.id'), nullable = False)
    key = db.Column(db.Unicode(255), index = True)
    value = db.Column(db.UnicodeText(512 * 1024 * 1024)) # 512 MB
    datetime = db.Column(db.DateTime, index = True)

    rlms = relation(RLMS.__name__, backref = backref('caches', order_by=id, cascade = 'all,delete'))

    def __init__(self, rlms_id, key, value, datetime):
        self.rlms_id = rlms_id
        self.key = key
        self.value = value
        self.datetime = datetime

#######################################################################
# 
#     Laboratory
# 
#  1 Laboratory is the minimum representation that can be reserved.
# 

class Laboratory(db.Model, SBBase):
    __tablename__ = 'laboratories'
    __table_args__ = (db.UniqueConstraint('laboratory_id', 'rlms_id'), TABLE_KWARGS)

    id = db.Column(db.Integer, primary_key = True)

    name                     = db.Column(db.Unicode(255), nullable = False)
    laboratory_id            = db.Column(db.Unicode(255), nullable = False)
    rlms_id                  = db.Column(db.Integer, db.ForeignKey('rlmss.id'), nullable = False)
    visibility               = db.Column(db.Unicode(50), nullable = False, index = True, default = u'private')
    available                = db.Column(db.Boolean, nullable = False, index = True, default = False)
    default_local_identifier = db.Column(db.Unicode(50), nullable = False, default = u"")
    publicly_available       = db.Column(db.Boolean, nullable = False, index = True, default = False)
    # Not unique: otherwise there wouldn't be more than one with '' as value
    public_identifier        = db.Column(db.Unicode(50), nullable = False, default = u"")
    go_lab_reservation       = db.Column(db.Boolean, nullable = False, index = True, default = False)

    rlms          = relation(RLMS.__name__, backref = backref('laboratories', order_by=id, cascade = 'all,delete'))

    def __init__(self, name = None, laboratory_id = None, rlms = None, visibility = None, available = None):
        self.name          = name
        self.laboratory_id = laboratory_id
        self.rlms          = rlms
        self.visibility    = visibility
        self.available     = available

    def __unicode__(self):
        return gettext(u"%(name)s at %(rlms)s", name=self.name, rlms=self.rlms)

#######################################################################
#
#     LearningTool
# 
# 1 LearningTool (or CMS or PLE) is a system that manages authentication and
# authorization. It is divided into multiple courses (see below).
# 

class LearningTool(db.Model, SBBase):
    __tablename__  = 'learning_tools'
    __table_args__ = (db.UniqueConstraint('name'), db.UniqueConstraint('full_name'), TABLE_KWARGS)
    id = db.Column(db.Integer, primary_key = True)
    name      = db.Column(db.Unicode(50), nullable = False, index = True)
    full_name = db.Column(db.Unicode(50), nullable = False, index = True)
    url       = db.Column(db.Unicode(300), nullable = False)

    def __init__(self, name = None, full_name = None, url = None):
        self.name = name
        self.full_name = full_name
        self.url = url

    def __repr__(self):
        return "LearningTool(%(lmsname)r, %(lmsfullname)r, %(lmsurl)r)" % dict(lmsname=self.name, lmsfullname=self.full_name, lmsurl=self.url)

    def __unicode__(self):
        return self.name

##################################################
# 
#         LT Basic HTTP Credentials
# 
#   Used by LTs to authenticate in the system
# 

class BasicHttpCredentials(db.Model, SBBase):
    __tablename__  = 'basic_http_credentials'
    __table_args__ = (db.UniqueConstraint('lt_login'), db.UniqueConstraint('lt_id'), TABLE_KWARGS)
    id        = db.Column(db.Integer, primary_key = True)
    lt_id        = db.Column(db.Integer, db.ForeignKey('learning_tools.id'), nullable = False)

    # Arguments for the LT to connect the LabManager
    lt_login     = db.Column(db.Unicode(50), nullable = False)
    lt_password  = db.Column(db.Unicode(50), nullable = False)

    # Arguments for the LabManager to connect the LT. Might be null
    lt_url       = db.Column(db.Unicode(300), nullable = True)
    labmanager_login    = db.Column(db.Unicode(50), nullable = True)
    labmanager_password = db.Column(db.Unicode(50), nullable = True)

    lt = relation('LearningTool', backref=backref('basic_http_authentications', order_by=id, cascade='all, delete'))

    def __init__(self, lt_login = None, lt_password = None, lt = None, lt_url = None, labmanager_login = None, labmanager_password = None):
        self.lt                  = lt
        self.lt_login            = lt_login
        self.lt_password         = lt_password
        self.lt_url              = lt_url
        self.labmanager_login    = labmanager_login
        self.labmanager_password = labmanager_password

    def __repr__(self):
        return "BasicHttpCredentials(lt_login=%(lmslogin)r, lt_password=%(lmspassword)r, lt=%(lmslms)r, lt_url=%(lmsurl)r, labmanager_login=%(labmanlogin)r, labmanager_password=%(labmanpassword)r)" % dict(lmslogin=self.lt_login, lmspassword=self.password, lmslms=self.lt, lmsurl=self.lt_url, labmanlogin=self.labmanager_login, labmanpassword=self.labmanager_password)

    def __unicode__(self):
        return gettext(u"Basic HTTP auth for %(name)s", name=self.lt.name)

    def update_password(self, old_password):
        if self.lt_password != old_password:
            self.lt_password = hashlib.new('sha', self.lt_password.encode('utf8')).hexdigest()

##################################################
# 
#         LT Shindig credentials
# 
#   Used by LTs to authenticate in the system
# 

class ShindigCredentials(db.Model, SBBase):
    __tablename__  = 'shindig_credentials'
    __table_args__ = (db.UniqueConstraint('lt_id'), TABLE_KWARGS)
    id        = db.Column(db.Integer, primary_key = True)
    lt_id        = db.Column(db.Integer, db.ForeignKey('learning_tools.id'), nullable = False)

    # The URL of the Shindig server. Example: http://shindig.epfl.ch (no trailing slash)
    shindig_url   = db.Column(db.Unicode(50), nullable = False)

    lt = relation('LearningTool', backref=backref('shindig_credentials', order_by=id, cascade='all, delete'))

    def __init__(self, lt = None, shindig_url = None):
        self.lt         = lt
        self.shindig_url = shindig_url

    def __repr__(self):
        return "ShindigCredentials(lt=%(lmslms)r, shindig_url=%(shindigurl)r)" % dict(lmslms=self.lt, shindigurl=self.shindig_url)

    def __unicode__(self):
        return gettext(u"ShindigCredentials for %(lmsname)s", lmsname=self.lt.name)

##################################################
# 
#                   LT User
# 
#   LT Users (administrators or teachers) can
#   authenticate and change stuff at LT level.
#  

users2courses_relation = db.Table('users2courses',
    db.Column('course_id',  db.Integer, db.ForeignKey('courses.id')),
    db.Column('lt_user_id', db.Integer, db.ForeignKey('lt_users.id'))
)

class LtUser(db.Model, SBBase, UserMixin):
    __tablename__  = 'lt_users'
    __table_args__ = (db.UniqueConstraint('login','lt_id'), TABLE_KWARGS)
    id           = db.Column(db.Integer, primary_key = True)
    login        = db.Column(db.Unicode(50), nullable = False, index = True)
    full_name    = db.Column(db.Unicode(50), nullable = False)
    password     = db.Column(db.Unicode(128), nullable = False)
    access_level = db.Column(db.Unicode(50), nullable = False)
    lt_id    = db.Column(db.Integer, db.ForeignKey('learning_tools.id'), nullable = False)

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
        return u"%(lmslogin)s@%(lmsname)s" % dict(lmslogin=self.login, lmsname=self.lt.name)
    
    def get_id(self):
        return u"lt_user::%s::%s" %  (self.lt.name, self.login)

    @classmethod
    def exists(self, login, word, lt_id):
        return db.session.query(self).filter_by(login = login, password = word, lt_id = int(lt_id)).first()    

#####################################################################################
# 
#    Course
# 
#  1 Course is part of a LT and it will have permission on certain laboratories
# 

class Course(db.Model, SBBase):
    __tablename__ = 'courses'
    __table_args__ = (db.UniqueConstraint('lt_id','context_id'), TABLE_KWARGS)
    id = db.Column(db.Integer, primary_key = True)
    lt_id = db.Column(db.Integer, db.ForeignKey('learning_tools.id'), nullable = False)
    name = db.Column(db.Unicode(50), nullable = False)
    context_id = db.Column(db.Unicode(50), nullable = False)

    lt = relation('LearningTool', backref=backref('courses', order_by=id, cascade='all, delete'))

    def __init__(self, name = None, lt = None, context_id = None):
        self.name = name
        self.lt   = lt
        self.context_id = context_id

    def __repr__(self):
        return "Course(name=%(coursename)r, lt=%(courselms)r, context_id=%(coursecontext)r)" % dict(coursename=self.name, courselms=self.lt, coursecontext=self.context_id)

    def __unicode__(self):
        return gettext(u"%(coursename)s on %(courselms)s", coursename=self.name, courselms=self.lt)

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

class PermissionToLt(db.Model, SBBase):
    __tablename__ = 'permissions2lt'
    __table_args__ = (db.UniqueConstraint('laboratory_id', 'lt_id'), db.UniqueConstraint('local_identifier', 'lt_id'), TABLE_KWARGS)
    id = db.Column(db.Integer, primary_key = True)
    local_identifier     = db.Column(db.Unicode(100), nullable = False, index = True)
    laboratory_id = db.Column(db.Integer, db.ForeignKey('laboratories.id'), nullable = False)
    lt_id        = db.Column(db.Integer, db.ForeignKey('learning_tools.id'),  nullable = False)
    configuration = db.Column(db.Unicode(10 * 1024)) # JSON document
    accessible    = db.Column(db.Boolean, nullable = False, index = True, default = False)

    laboratory = relation(Laboratory.__name__,  backref = backref('lab_permissions', order_by=id, cascade = 'all,delete'))
    lt        = relation(LearningTool.__name__, backref = backref('lab_permissions', order_by=id, cascade = 'all,delete'))

    def __init__(self, lt = None, laboratory = None, configuration = None, local_identifier = None, accessible = None):
        self.lt               = lt
        self.laboratory       = laboratory
        self.configuration    = configuration
        self.local_identifier = local_identifier
        self.accessible       = accessible

    def __unicode__(self):
        return gettext(u"%(identifier)s: lab %(labname)s to %(lmsname)s", identifier=self.local_identifier, labname=self.laboratory.name, lmsname=self.lt.name)

########################################################
# 
#     PermissionToLtUser
#
# Defines that a LT User has permission on a Laboratory.
#

class PermissionToLtUser(db.Model, SBBase):
    __tablename__  = 'permissions2ltuser'
    __table_args__ = (db.UniqueConstraint('permission_to_lt_id', 'lt_user_id'), TABLE_KWARGS)
    id = db.Column(db.Integer, primary_key = True)
    permission_to_lt_id = db.Column(db.Integer, db.ForeignKey('permissions2lt.id'), nullable = False, index = True)
    lt_user_id          = db.Column(db.Integer, db.ForeignKey('lt_users.id'), nullable = False, index = True)
    
    # LTI data
    key                  = db.Column(db.Unicode(100), nullable = False, unique = True)
    secret               = db.Column(db.Unicode(100), nullable = False)

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

class PermissionToCourse(db.Model, SBBase):
    __tablename__  = 'permissions2course'
    __table_args__ = (db.UniqueConstraint('permission_to_lt_id', 'course_id'), TABLE_KWARGS)
    id = db.Column(db.Integer, primary_key = True)
    configuration = db.Column(db.Unicode(10 * 1024), nullable = True)
    permission_to_lt_id = db.Column(db.Integer, db.ForeignKey('permissions2lt.id'), nullable = False)
    course_id            = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable = False)

    permission_to_lt = relation('PermissionToLt', backref=backref('course_permissions', order_by=id, cascade='all, delete'))
    course            = relation('Course', backref=backref('permissions', order_by=id, cascade='all, delete'))

    def __init__(self, course = None, permission_to_lt = None, configuration = None):
        self.course            = course
        self.configuration     = configuration
        self.permission_to_lt = permission_to_lt

    def __repr__(self):
        return "PermissionToCourse(course=%(coursecourse)r, configuration=%(courseconfiguration)r, permission_to_lt=%(coursepermission)r)" % dict(coursecourse=self.course, courseconfiguration=self.configuration, coursepermission=self.permission_to_lt)

    def __unicode__(self):
        return gettext(u"%(coursename)s from %(lmsname)s on %(permission)s", coursename=self.course.name, lmsname=self.course.lt.name, permission=self.permission_to_lt)

########################################################
# 
#     RequestPermissionLT
#
#     When a school requests permission to use a lab, and the labmanager admin must grant or reject this request.
#     If the request is granted, a new entry is created in PermissionToLt

class RequestPermissionLT(db.Model, SBBase):
    __tablename__ = 'request_permissions_lt'
    __table_args__ = (db.UniqueConstraint('laboratory_id', 'lt_id'), db.UniqueConstraint('local_identifier', 'lt_id'), TABLE_KWARGS)
    id = db.Column(db.Integer, primary_key = True)
    local_identifier     = db.Column(db.Unicode(100), nullable = False, index = True)
    laboratory_id = db.Column(db.Integer, db.ForeignKey('laboratories.id'), nullable = False)
    lt_id        = db.Column(db.Integer, db.ForeignKey('learning_tools.id'),  nullable = False)
    configuration = db.Column(db.Unicode(10 * 1024)) # JSON document
    accessible    = db.Column(db.Boolean, nullable = False, index = True, default = False)

    laboratory = relation(Laboratory.__name__,  backref = backref('lab_requestpermissions', order_by=id, cascade = 'all,delete'))
    lt        = relation(LearningTool.__name__, backref = backref('lab_requestpermissions', order_by=id, cascade = 'all,delete'))

    def __init__(self, lt = None, laboratory = None, configuration = None, local_identifier = None, accessible = None):
        self.lt              = lt
        self.laboratory       = laboratory
        self.configuration    = configuration
        self.local_identifier = local_identifier
        self.accessible       = accessible

    def __unicode__(self):
        return gettext(u"'%(localidentifier)s': lab %(labname)s to %(ltname)s", localidentifier=self.local_identifier, 
                                                                                                                            labname = self.laboratory.name, 
                                                                                                                            ltname = self.lt.name)

class EmbedApplication(db.Model):
    __tablename__ = 'EmbedApplications'

    id = db.Column(db.Integer, primary_key = True)
    url = db.Column(db.Unicode(255), index = True, nullable = False)
    name = db.Column(db.Unicode(100), index = True, nullable = False)
    owner_id = db.Column(db.Integer, ForeignKey('siway_user.id'))
    height = db.Column(db.Integer)
    scale = db.Column(db.Integer) # value multiplied by 100; 9850 represents 98.5
    identifier = db.Column(db.Unicode(36), index = True, nullable = False, unique = True)
    creation = db.Column(db.DateTime, index = True, nullable = False)
    last_update = db.Column(db.DateTime, index = True, nullable = False)
    description = db.Column(db.UnicodeText, nullable = True)
    age_ranges_commas = db.Column(db.Unicode(100), nullable = True) # golab format, comma separated
    domains_json = db.Column(db.Unicode(255), nullable = True) # JSON-encoded domains in a list

    owner = relation('SiWaySAMLUser',backref="embed_applications")

    def __init__(self, url, name, owner, height = None, identifier = None, creation = None, last_update = None, scale = None, description = None, age_ranges_range=None, domains=None):
        if creation is None:
            creation = datetime.datetime.utcnow()
        if last_update is None:
            last_update = datetime.datetime.utcnow()
        if identifier is None:
            identifier = unicode(uuid.uuid4())
            while EmbedApplication.query.filter_by(identifier=identifier).first() is not None:
                identifier = unicode(uuid.uuid4())
        self.url = url
        self.name = name
        self.owner = owner
        self.identifier = identifier
        self.creation = creation
        self.last_update = last_update
        self.height = height
        self.scale = scale
        self.description = description
        self.age_ranges_range = age_ranges_range
        self.domains = domains

    @property
    def domains(self):
        if not self.domains_json:
            return []
        return json.loads(self.domains_json) or []

    @domains.setter
    def domains(self, domains):
        self.domains_json = json.dumps(domains or [])

    @property
    def domains_text(self):
        return ', '.join(self.domains)

    @domains_text.setter
    def domains_text(self, domains):
        self.domains = [ domain.strip() for domain in domains.split(',') if domain.strip() ]

    @property
    def age_ranges(self):
        if not self.age_ranges_commas:
            return []
        return self.age_ranges_commas.split(',')

    @age_ranges.setter
    def age_ranges(self, age_ranges):
        self.age_ranges_commas = ','.join(age_ranges or [])

    @property
    def age_ranges_range(self):
        age_ranges = self.age_ranges
        if age_ranges[0] == '<6':
            minimum = 4
        elif age_ranges[0] == '>18':
            minimum = 20
        else:
            minimum = int(age_ranges[0].split('-')[0])
        if age_ranges[-1] == '<6':
            maximum = 4
        elif age_ranges[-1] == '>18':
            maximum = 20
        else:
            maximum = int(age_ranges[-1].split('-')[1])

        if maximum == 20 and minimum == 20:
            minimum = 18
        if minimum == 4 and maximum == 4:
            maximum = 6

        return "[%s, %s]" % (minimum, maximum)

    @age_ranges_range.setter
    def age_ranges_range(self, age_ranges_range):
        age_ranges_splitted = age_ranges_range[1:-1].split(',')
        min_age = int(age_ranges_splitted[0].strip())
        max_age = int(age_ranges_splitted[1].strip())
        
        new_age_ranges = []
        for x in xrange(min_age, max_age + 2, 2):
            if x == 4:
                new_age_ranges.append('<6')
            elif x == 6:
                new_age_ranges.append('6-8')
            elif x == 8:
                new_age_ranges.append('8-10')
            elif x == 10:
                new_age_ranges.append('10-12')
            elif x == 12:
                new_age_ranges.append('12-14')
            elif x == 14:
                new_age_ranges.append('14-16')
            elif x == 16:
                new_age_ranges.append('16-18')
            elif x == 18:
                new_age_ranges.append('>18')
            elif x == 20 and '>18' not in new_age_ranges:
                new_age_ranges.append('>18')
        self.age_ranges = new_age_ranges

    def update(self, url = None, name = None, height = None, scale = None, description = None, domains = None, age_ranges_range = None, domains_text=None):
        if url is not None:
            self.url = url
        if name is not None:
            self.name = name
        if height is not None:
            self.height = height
        if scale is not None:
            self.scale = scale
        if description is not None:
            self.description = description
        if domains is not None:
            self.domains = domains
        if age_ranges_range is not None:
            self.age_ranges_range = age_ranges_range
        if self.domains_text is not None:
            self.domains_text = domains_text
        self.last_update = datetime.datetime.utcnow()

class EmbedApplicationTranslation(db.Model):
    __tablename__ = 'EmbedApplicationTranslation'

    id = db.Column(db.Integer, primary_key = True)
    embed_application_id = db.Column(db.Integer, ForeignKey('EmbedApplications.id'))
    url = db.Column(db.Unicode(255), index = True, nullable = False)
    language = db.Column(db.Unicode(10), index = True, nullable = False)

    embed_application = relation("EmbedApplication", backref="translations")

    def __init__(self, embed_application, url, language):
        self.embed_application = embed_application
        self.url = url
        self.language = language

from labmanager.rlms import get_manager_class

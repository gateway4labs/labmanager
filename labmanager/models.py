from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relation, backref
from labmanager.database import Base

class LMS(Base):

    __tablename__ = 'LMSs'

    id = Column(Integer, primary_key=True)

    login    = Column(String(50),  unique=True)
    name     = Column(String(50))
    password = Column(String(50)) # hash

    def __init__(self, login = None, name = None, password = None):
        self.login    = login
        self.name     = name
        self.password = password

    def __repr__(self):
        return 'LMS(%r, %r, %r)' % (self.login, self.name, self.password)

class LabManagerUser(Base):
    __tablename__ = 'LabManagerUsers'

    id = Column(Integer, primary_key=True)

    login    = Column(String(50),  unique = True ) 
    name     = Column(String(50) )
    password = Column(String(50)) # hash

    def __init__(self, login = None, name = None, password = None):
        self.login    = login
        self.name     = name
        self.password = password

    def __repr__(self):
        return 'LabManagerUser(%r, %r, %r)' % (self.login, self.name, self.password)


class RLMSType(Base):
    __tablename__ = 'RLMS_types'

    id = Column(Integer, primary_key = True)

    name    = Column(String(50), unique = True)

    def __init__(self, name = None):
        self.name = name

    def __repr__(self):
        return 'RLMSType(%r)' % self.name

class RLMSTypeVersion(Base):
    __tablename__  = 'RLMS_type_versions'
    __table_args__ = (UniqueConstraint('rlms_type_id', 'version'), )

    id = Column(Integer, primary_key = True)

    rlms_type_id = Column(Integer, ForeignKey('RLMS_types.id'), nullable = False)
    version = Column(String(50))

    rlms_type = relation(RLMSType.__name__, backref = backref('versions', order_by=id, cascade = 'all,delete'))

    def __init__(self, rlms_type = None, version = None):
        self.rlms_type = rlms_type
        self.version   = version


class RLMS(Base):
    __tablename__ = 'RLMSs'
    
    id = Column(Integer, primary_key = True)

    name     = Column(String(50), nullable = False)
    location = Column(String(50), nullable = False)
    rlms_version_id = Column(Integer, ForeignKey('RLMS_type_versions.id'), nullable = False)

    configuration = Column(String(10 * 1024)) # JSON document
    
    rlms_version = relation(RLMSTypeVersion.__name__, backref = backref('rlms', order_by=id, cascade = 'all,delete'))

    def __init__(self, name = None, location = None, rlms_version = None, configuration = None):
        self.name          = name
        self.location      = location
        self.rlms_version  = rlms_version
        self.configuration = configuration

class PermissionOnLMS(Base):
    __tablename__ = 'PermissionOnLMSs'

    id = Column(Integer, primary_key = True)

    rlms_id = Column(Integer, ForeignKey('RLMSs.id'), nullable = False)
    lms_id  = Column(Integer, ForeignKey('LMSs.id'),  nullable = False)

    configuration = Column(String(10 * 1024)) # JSON document

    rlms = relation(RLMS.__name__,  backref = backref('permissions', order_by=id, cascade = 'all,delete'))
    lms  = relation(LMS.__name__, backref = backref('permissions', order_by=id, cascade = 'all,delete'))

    def __init__(self, lms = None, rlms = None, configuration = None):
        self.lms           = lms
        self.rlms          = rlms
        self.configuration = configuration


class Course(Base):
    __tablename__  = 'Courses'
    __table_args__ = (UniqueConstraint('course_id', 'lms_id'), )

    id = Column(Integer, primary_key = True)

    # The ID in the remote LMS
    course_id = Column(String(50), nullable = False)

    name   = Column(String(50), nullable = False)

    lms_id = Column(Integer, ForeignKey('LMSs.id'), nullable = False)

    lms  = relation(LMS.__name__, backref = backref('courses', order_by=id, cascade = 'all,delete'))

    def __init__(self, lms = None, course_id = None, name = None):
        self.course_id = course_id
        self.name      = name
        self.lms       = lms

class PermissionOnCourse(Base):
    __tablename__  = 'PermissionOnCourses'
    
    id = Column(Integer, primary_key = True)

    configuration        = Column(String(10 * 1024)) # JSON document

    permission_on_lms_id = Column(Integer, ForeignKey('PermissionOnLMSs.id'), nullable = False)

    permission_on_lms    = relation(PermissionOnLMS.__name__, backref = backref('course_permissions', order_by=id, cascade = 'all,delete'))

    def __init__(self, permission_on_lms = None, configuration = None):
        self.permission_on_lms = permission_on_lms
        self.configuration     = configuration


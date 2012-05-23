from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relation, backref
from labmanager.database import Base

class LMS(Base):

    __tablename__ = 'LMSs'

    id = Column(Integer, primary_key=True)


    name                = Column(String(50), nullable = False)
    url                 = Column(String(50), nullable = False) # remote url

    lms_login           = Column(String(50), nullable = False, unique=True)
    lms_password        = Column(String(50), nullable = False) # hash
    
    labmanager_login    = Column(String(50), nullable = False)
    labmanager_password = Column(String(50), nullable = False) # plaintext: my password there

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

    login    = Column(String(50),  unique = True ) 
    name     = Column(String(50) )
    password = Column(String(50)) # hash

    def __init__(self, login = None, name = None, password = None):
        self.login    = login
        self.name     = name
        self.password = password


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

class Laboratory(Base):
    __tablename__ = 'Laboratories'

    id = Column(Integer, primary_key = True)

    name          = Column(String(50), nullable = False)
    laboratory_id = Column(String(50), nullable = False)
    rlms_id       = Column(Integer, ForeignKey('RLMSs.id'), nullable = False)

    rlms          = relation(RLMS.__name__, backref = backref('laboratories', order_by=id, cascade = 'all,delete'))

    def __init__(self, name = None, laboratory_id = None, rlms = None):
        self.name          = name
        self.laboratory_id = laboratory_id
        self.rlms          = rlms


class PermissionOnLaboratory(Base):
    __tablename__ = 'PermissionOnLaboratories'

    id = Column(Integer, primary_key = True)

    laboratory_id = Column(Integer, ForeignKey('Laboratories.id'), nullable = False)
    lms_id        = Column(Integer, ForeignKey('LMSs.id'),  nullable = False)

    configuration = Column(String(10 * 1024)) # JSON document

    laboratory = relation(Laboratory.__name__,  backref = backref('permissions', order_by=id, cascade = 'all,delete'))
    lms        = relation(LMS.__name__, backref = backref('permissions', order_by=id, cascade = 'all,delete'))

    def __init__(self, lms = None, laboratory = None, configuration = None):
        self.lms           = lms
        self.laboratory    = laboratory
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

    permission_on_lms_id = Column(Integer, ForeignKey('PermissionOnLaboratories.id'), nullable = False)

    permission_on_lms    = relation(PermissionOnLaboratory.__name__, backref = backref('course_permissions', order_by=id, cascade = 'all,delete'))

    def __init__(self, permission_on_lms = None, configuration = None):
        self.permission_on_lms = permission_on_lms
        self.configuration     = configuration


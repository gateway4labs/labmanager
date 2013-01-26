# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode, ForeignKey, UniqueConstraint, sql
from sqlalchemy.orm import relation, backref
from labmanager.database import Base, db_session as DBS

from labmanager.models import LMS, SBBase, PermissionOnLaboratory

class NewCourse(Base, SBBase):
    __tablename__ = 'newcourses'
    id = Column(Integer, primary_key = True)
    lms_id = Column(Integer, ForeignKey('newlmss.id'), nullable = False)
    name = Column(Unicode(50), nullable = False)
    context_id = Column(Unicode(50), nullable = False)

    lms = relation('NewLMS', backref=backref('courses', order_by=id, cascade='all, delete'))

    def __init__(self, name = None, lms = None, context_id = None):
        self.name = name
        self.lms = lms
        self.context_id = context_id

    def __repr__(self):
        return "<NewCourse: %s LMS:%s>" % (self.name, self.lms)

    def __unicode__(self):
        return "%s on %s" % (self.name, self.lms)

    @classmethod
    def find_by_lms_and_context(self, lms, context):
        return DBS.query(self).filter(sql.and_(self.lms == lms,
                                               self.context_id == context)).first()

    @classmethod
    def find_or_create(self, lms, context, name=None):
        instance = self.find_by_lms_and_context(lms, context)
        if instance:
            return instance
        else:
            return self.new(name = name, lms = lms, context_id = context)



##########

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

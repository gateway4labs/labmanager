# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode, ForeignKey, UniqueConstraint, sql
from sqlalchemy.orm import relation, backref
from labmanager.database import Base, db_session as DBS

from labmanager.models import SBBase


class Permission(Base, SBBase):

    __tablename__  = 'permissions'
    __table_args__ = (UniqueConstraint('permission_on_lab_id', 'course_id'),)

    id = Column(Integer, primary_key = True)

    access = Column(Unicode(50), nullable = False)
    configuration = Column(Unicode(10 * 1024), nullable = True)

    permission_on_lab_id = Column(Integer, ForeignKey('PermissionOnLaboratories.id'), nullable = False)
    course_id            = Column(Integer, ForeignKey('newcourses.id'), nullable = False)


    permission_on_lab = relation('PermissionOnLaboratory', backref=backref('course_permissions', order_by=id, cascade='all, delete'))
    course            = relation('NewCourse', backref=backref('permissions', order_by=id, cascade='all, delete'))
    
    # TODO: context or course: select one
    def __init__(self, context = None, permission_on_lab = None, configuration = None, access = None):
        self.course            = context
        self.configuration     = configuration
        self.permission_on_lab = permission_on_lab
        self.access            = access

    def __repr__(self):
        return "<Permission %r: %r %r>" % (self.id, self.permission_on_lab.laboratory_id, self.access)

    def __unicode__(self):
        return u"%s from %s on %s (%s)" % (self.newcourse.name, self.course.lms.name, self.laboratory.name, self.access)

    def change_status(self, new_status):
        self.access = new_status
        DBS.commit()

    @classmethod
    def find_by_status(self, status):
        return DBS.query(self).filter(self.access == status).all()

    @classmethod
    def find_with_params(self, lms = None, context = None):
        return DBS.query(self).filter(sql.and_(self.newlms == lms,
                                               self.newcourse == context)
                                      ).first()

    @classmethod
    def find_with_lms_context_exp(self, lms, context, laboratory):
        return DBS.query(self).filter(sql.and_(self.newlms == lms,
                                               self.laboratory == laboratory,
                                               self.newcourse == context)
                                      ).first()

    @classmethod
    def find_all_with_lms_and_context(self, lms, context):
        return DBS.query(self).filter(sql.and_(self.newlms == lms,
                                               self.newcourse == context)
                                      ).all()

    @classmethod
    def find_or_create(self, lms, context, laboratory):
        instance = self.find_with_lms_context_exp(lms = lms, context = context,
                                                  laboratory = laboratory)
        if instance:
            return instance
        else:
            return self.new(lms = lms, context = context, laboratory = laboratory, access = u'pending')

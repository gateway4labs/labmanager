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
    course_id            = Column(Integer, ForeignKey('courses.id'), nullable = False)


    permission_on_lab = relation('PermissionOnLaboratory', backref=backref('course_permissions', order_by=id, cascade='all, delete'))
    course            = relation('Course', backref=backref('permissions', order_by=id, cascade='all, delete'))

    # TODO: context or course: select one
    def __init__(self, context = None, permission_on_lab = None,
                 configuration = None, access = u"pending"):
        self.course            = context
        self.configuration     = configuration
        self.permission_on_lab = permission_on_lab
        self.access            = access

    def __repr__(self):
        return "<Permission %r: %r %r>" % (self.id,
                                           self.permission_on_lab.laboratory_id,
                                           self.access)

    def __unicode__(self):
        return u"%s from %s on %s (%s)" % (self.course.name,
                                           self.course.lms.name,
                                           self.laboratory.name,
                                           self.access)

    def change_status(self, new_status):
        self.access = new_status
        DBS.commit()

    @classmethod
    def find_by_status(self, status):
        return DBS.query(self).filter(self.access == status).all()

    @classmethod
    def find_all_for_context(self, context):
        return DBS.query(self).filter(self.course == context).all()

    @classmethod
    def find_or_create(self, context, perm_on_lab):
        instance = DBS.query(self).filter(sql.and_(self.course == context,
                                                   self.permission_on_lab == perm_on_lab)
                                          ).first()
        if instance:
            return instance
        else:
            return self.new(context = context, permission_on_lab = perm_on_lab)

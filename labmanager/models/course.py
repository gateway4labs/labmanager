# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode, ForeignKey, sql
from sqlalchemy.orm import relation, backref
from labmanager.database import Base, db_session as DBS

from labmanager.models import SBBase

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


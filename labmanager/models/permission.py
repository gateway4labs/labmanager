# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode, ForeignKey, UniqueConstraint, sql
from sqlalchemy.orm import relation, backref
from labmanager.database import Base, db_session as DBS

from labmanager.models import SBBase


class Permission(Base, SBBase):
    __tablename__  = 'permissions'
    id = Column(Integer, primary_key = True)
    access = Column(Unicode(50), nullable = False)
    experiment_id = Column(Integer, ForeignKey('experiments.id'), nullable = False)
    lms_id = Column(Integer, ForeignKey('newlmss.id'), nullable = False)
    course_id = Column(Integer, ForeignKey('newcourses.id'), nullable = False)
#    resource_link_id = Column(Integer)
    configuration = Column(Unicode(10 * 1024), nullable = True)

    def __init__(self, lms = None, context = None, experiment = None,
                 access = u"pending"):
        self.newlms = lms
        self.newcourse = context
        self.experiment = experiment
        self.access = access

    def __repr__(self):
        return "<Permission %d: %s LMS:%s %s>" % (self.id, self.experiment_id,
                                                  self.lms_id, self.access)

    def __unicode__(self):
        return "%s from %s on %s (%s)" % (self.newcourse.name, self.newlms.name,
                                          self.experiment.name, self.access)

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
    def find_with_lms_context_exp(self, lms, context, experiment):
        return DBS.query(self).filter(sql.and_(self.newlms == lms,
                                               self.experiment == experiment,
                                               self.newcourse == context)
                                      ).first()

    @classmethod
    def find_all_with_lms_and_context(self, lms, context):
        return DBS.query(self).filter(sql.and_(self.newlms == lms,
                                               self.newcourse == context)
                                      ).all()

    @classmethod
    def find_or_create(self, lms, context, experiment):
        instance = self.find_with_lms_context_exp(lms = lms, context = context,
                                                  experiment = experiment)
        if instance:
            return instance
        else:
            return self.new(lms = lms, context = context, experiment = experiment)

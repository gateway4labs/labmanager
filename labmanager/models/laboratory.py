# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode, ForeignKey, UniqueConstraint, sql
from sqlalchemy.orm import relation, backref
from labmanager.database import Base, db_session as DBS

from labmanager.models import RLMS, NewLMS

class Laboratory(Base):
    __tablename__ = 'laboratories'
    __table_args__ = (UniqueConstraint('laboratory_id', 'rlms_id'), )

    id = Column(Integer, primary_key = True)

    name          = Column(Unicode(50), nullable = False)
    laboratory_id = Column(Unicode(50), nullable = False)
    rlms_id       = Column(Integer, ForeignKey('rlmss.id'), nullable = False)

    rlms          = relation(RLMS.__name__, backref = backref('laboratories', order_by=id, cascade = 'all,delete'))

    def __init__(self, name = None, laboratory_id = None, rlms = None):
        self.name          = name
        self.laboratory_id = laboratory_id
        self.rlms          = rlms

    def __unicode__(self):
        return u'%s at %s' % (self.name, self.rlms)

class PermissionOnLaboratory(Base):
    __tablename__ = 'PermissionOnLaboratories'
    __table_args__ = (UniqueConstraint('laboratory_id', 'lms_id'), UniqueConstraint('local_identifier', 'lms_id'))

    id = Column(Integer, primary_key = True)

    local_identifier     = Column(Unicode(100), nullable = False, index = True)

    laboratory_id = Column(Integer, ForeignKey('laboratories.id'), nullable = False)
    lms_id        = Column(Integer, ForeignKey('newlmss.id'),  nullable = False)

    configuration = Column(Unicode(10 * 1024)) # JSON document

    laboratory = relation(Laboratory.__name__,  backref = backref('lab_permissions', order_by=id, cascade = 'all,delete'))
    lms        = relation(NewLMS.__name__, backref = backref('lab_permissions', order_by=id, cascade = 'all,delete'))

    def __init__(self, lms = None, laboratory = None, configuration = None, local_identifier = None):
        self.lms              = lms
        self.laboratory       = laboratory
        self.configuration    = configuration
        self.local_identifier = local_identifier

    def __unicode__(self):
        return u"'%s': lab %s to %s" % (self.local_identifier, self.laboratory.name, self.lms.name)

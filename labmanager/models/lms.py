# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relation, backref
from labmanager.database import Base

from labmanager.models import SBBase

class LMS(Base, SBBase):

    __tablename__  = 'lmss'
    __table_args__ = (UniqueConstraint('name'), )

    id = Column(Integer, primary_key = True)
    name = Column(Unicode(50), nullable = False, index = True)
    url = Column(Unicode(300), nullable = False)

    def __init__(self, name = None, url = None):
        self.name = name
        self.url = url

    def __repr__(self):
        return "<LMS:%s %s>" % (self.id, self.name)

    def __unicode__(self):
        return self.name

class LMSUser(Base):
    __tablename__  = 'lmsusers'
    __table_args__ = (UniqueConstraint('login','lms_id'), )

    id        = Column(Integer, primary_key = True)

    login     = Column(Unicode(50), nullable = False, index = True)
    full_name = Column(Unicode(50), nullable = False)
    password  = Column(Unicode(128), nullable = False)

    lms_id    = Column(Integer, ForeignKey('lmss.id'), nullable = False)

    lms       = relation('LMS', backref = backref('users', order_by=id, cascade = 'all,delete'))

    def __init__(self, login = None, full_name = None, lms = None):
        self.login     = login
        self.full_name = full_name
        self.lms       = lms

    def __unicode__(self):
        return u'%s@%s' % (self.login, self.lms.name)
        



# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode, UniqueConstraint
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

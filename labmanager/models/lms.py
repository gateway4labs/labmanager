# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode, UniqueConstraint
from labmanager.database import Base

from labmanager.models import SBBase

class NewLMS(Base, SBBase):

    __tablename__  = 'newlmss'
    __table_args__ = (UniqueConstraint('name'), )

    id = Column(Integer, primary_key = True)
    name = Column(Unicode(50), nullable = False, index = True)
    url = Column(Unicode(300), nullable = False)

    def __init__(self, name = None, url = None):
        self.name = name
        self.url = url

    def __repr__(self):
        return "<NewLMS:%s %s>" % (self.id, self.name)

    def __unicode__(self):
        return self.name

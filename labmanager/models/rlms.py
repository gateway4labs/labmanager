# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode
from labmanager.database import Base

from labmanager.models import SBBase

class RLMS(Base, SBBase):
    __tablename__ = 'rlmss'
    id = Column(Integer, primary_key = True)
    kind = Column(Unicode(50), nullable = False)
    location = Column(Unicode(50), nullable = False)
    url = Column(Unicode(300), nullable = False)
    version = Column(Unicode(50), nullable = False)

    configuration = Column(Unicode(10 * 1024))

    def __init__(self, kind = None, url = None, location = None, version = None, configuration = '{}'):
        self.kind = kind
        self.location = location
        self.url = url
        self.version = version
        self.configuration = configuration

    def __repr__(self):
        return "RLMS(kind = %r, url=%r, location=%r, version=%r, configuration=%r" % (self.kind, self.url, self.location, self.version, self.configuration)

    def __unicode__(self):
        return u"%s on %s" % (self.kind, self.location)

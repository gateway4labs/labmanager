# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode, ForeignKey, UniqueConstraint, sql
from sqlalchemy.orm import relation, backref
from labmanager.database import Base, db_session as DBS

from labmanager.models import SBBase

# XXX DEPRECATED: TO BE DELETED
class LMS(Base):

    __tablename__ = 'LMSs'

    id = Column(Integer, primary_key=True)

    name                = Column(Unicode(50), nullable = False)
    url                 = Column(Unicode(300), nullable = False) # remote url

    lms_login           = Column(Unicode(50), nullable = False, unique=True)
    lms_password        = Column(Unicode(50), nullable = False) # hash

    labmanager_login    = Column(Unicode(50), nullable = False)
    labmanager_password = Column(Unicode(50), nullable = False) # plaintext: my password there

    def __init__(self, name = None, url = None, lms_login = None, lms_password = None, labmanager_login = None, labmanager_password = None):
        self.name                = name
        self.url                 = url
        self.lms_login           = lms_login
        self.lms_password        = lms_password
        self.labmanager_login    = labmanager_login
        self.labmanager_password = labmanager_password


class NewLMS(Base, SBBase):

    __tablename__  = 'newlmss'

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

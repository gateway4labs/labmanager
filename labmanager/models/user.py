# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode, ForeignKey, UniqueConstraint, sql
from sqlalchemy.orm import relation, backref
from labmanager.database import Base, db_session as DBS
from flask.ext.login import UserMixin

from labmanager.models import SBBase

class LabManagerUser(Base, SBBase, UserMixin):
    __tablename__ = 'LabManagerUsers'

    id = Column(Integer, primary_key=True)

    login    = Column(Unicode(50), unique = True )
    name     = Column(Unicode(50))
    password = Column(Unicode(50)) # hash
    access_level = Column(Unicode(50))

    def __init__(self, login = None, name = None, password = None, access_level = None):
        self.login    = login
        self.name     = name
        self.password = password
        self.access_level = access_level

    def __repr__(self):
        return "<LabMUser: %s level:%s>" % (self.name, self.access_level)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.access_level)


    @classmethod
    def exists(self, login, word):
        return DBS.query(self).filter(sql.and_(self.login == login, self.password == word)).first()

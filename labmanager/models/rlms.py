# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode, ForeignKey, UniqueConstraint, sql
from sqlalchemy.orm import relation, backref
from labmanager.database import Base, db_session as DBS

from labmanager.models import SBBase

class RLMSType(Base):
    __tablename__ = 'RLMS_types'

    id = Column(Integer, primary_key = True)

    name    = Column(Unicode(50), unique = True)

    def __init__(self, name = None):
        self.name = name

    def __repr__(self):
        return 'RLMSType(%r)' % self.name

class RLMSTypeVersion(Base):
    __tablename__  = 'RLMS_type_versions'
    __table_args__ = (UniqueConstraint('rlms_type_id', 'version'), )

    id = Column(Integer, primary_key = True)

    rlms_type_id = Column(Integer, ForeignKey('RLMS_types.id'), nullable = False)
    version = Column(Unicode(50))

    rlms_type = relation(RLMSType.__name__, backref = backref('versions', order_by=id, cascade = 'all,delete'))

    def __init__(self, rlms_type = None, version = None):
        self.rlms_type = rlms_type
        self.version   = version


class RLMS(Base):
    __tablename__ = 'RLMSs'

    id = Column(Integer, primary_key = True)

    name     = Column(Unicode(100), nullable = False)
    location = Column(Unicode(100), nullable = False)
    rlms_version_id = Column(Integer, ForeignKey('RLMS_type_versions.id'), nullable = False)

    configuration = Column(Unicode(10 * 1024)) # JSON document

    rlms_version = relation(RLMSTypeVersion.__name__, backref = backref('rlms', order_by=id, cascade = 'all,delete'))

    def __init__(self, name = None, location = None, rlms_version = None, configuration = None):
        self.name          = name
        self.location      = location
        self.rlms_version  = rlms_version
        self.configuration = configuration



class NewRLMS(Base, SBBase):
    __tablename__ = 'newrlmss'
    id = Column(Integer, primary_key = True)
    kind = Column(Unicode(50), nullable = False)
    location = Column(Unicode(50), nullable = False)
    url = Column(Unicode(300), nullable = False)
    version = Column(Unicode(50), nullable = False)

    experiments = relation('Experiment', backref=backref('newrlms', order_by=id))

    def __init__(self, kind = None, url = None, location = None, version = None):
        self.kind = kind
        self.location = location
        self.url = url
        self.version = version

    def __repr__(self):
        return "<NewRLMS: %s %s %s>" % (self.kind, self.version, self.location)

    def __unicode__(self):
        return "%s on %s" % (self.kind, self.location)

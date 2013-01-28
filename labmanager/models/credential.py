# -*-*- encoding: utf-8 -*-*-
from sqlalchemy import Column, Integer, Unicode, ForeignKey
from sqlalchemy.orm import relation, backref
from labmanager.database import Base, db_session as DBS

class Credential(Base):
    __tablename__  = 'credentials'
    id = Column(Integer, primary_key = True)
    key = Column(Unicode(50), nullable = False, unique=True)
    kind = Column(Unicode(50), nullable = False)
    lms_id = Column(Integer, ForeignKey('newlmss.id'), nullable = False)
    secret = Column(Unicode(50), nullable = False)

    lms = relation('NewLMS', backref=backref('authentications', order_by=id, cascade='all, delete'))

    def __init__(self, key = None, secret = None, kind = None, lms = None):
        self.key = key
        self.secret = secret
        self.kind = kind
        self.lms = lms

    def __repr__(self):
        return "<Credential: %s LMS:%s>" % ( self.lms_id, self.kind )

    def __unicode__(self):
        return "%s auth for %s" %(self.kind, self.lms.name)

    @classmethod
    def find_by_key(self, r_key):
        return DBS.query(self).filter( self.key == r_key ).first()


# -*-*- encoding: utf-8 -*-*-
import sha
from sqlalchemy import Column, Integer, Unicode, ForeignKey
from sqlalchemy.orm import relation, backref
from labmanager.database import Base, db_session as DBS
from labmanager.models import SBBase

class Credential(Base, SBBase):
    __tablename__  = 'credentials'
    id = Column(Integer, primary_key = True)
    key = Column(Unicode(50), nullable = False, unique=True)
    kind = Column(Unicode(50), nullable = False)
    lms_id = Column(Integer, ForeignKey('lmss.id'), nullable = False)
    secret = Column(Unicode(50), nullable = False)

    lms = relation('LMS', backref=backref('authentications', order_by=id, cascade='all, delete'))

    def __init__(self, key = None, secret = None, kind = None, lms = None):
        self.key = key
        self.secret = secret
        self.kind = kind
        self.lms = lms

    def __repr__(self):
        return "<Credential: lms_id: %s Kind: '%s' Key: '%s'>" % ( self.lms_id, self.kind, self.key )

    def __unicode__(self):
        return "%s auth for %s" %(self.kind, self.lms.name)

    @classmethod
    def find_by_key(self, r_key):
        return DBS.query(self).filter( self.key == r_key ).first()

    def update_password(self, old_secret):
        if self.secret != old_secret:
            self.secret = sha.new(self.secret).hexdigest()

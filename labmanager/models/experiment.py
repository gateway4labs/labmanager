# -*-*- encoding: utf-8 -*-*-

from sqlalchemy import Column, Integer, Unicode, ForeignKey, UniqueConstraint, sql
from sqlalchemy.orm import relation, backref
from labmanager.database import Base, db_session as DBS

class Experiment(Base):
    __tablename__  = 'experiments'
    id = Column(Integer, primary_key = True)
    name = Column(Unicode(50), nullable = False)
    rlms_id = Column(Integer, ForeignKey('newrlmss.id'), nullable = False)
    url = Column(Unicode(300), nullable = False)

    permissions = relation('Permission', backref=backref('experiment', order_by=id))

    def __init__(self, name = None, rlms = None, url = None):
        self.name = name
        self.newrlms = rlms
        self.url = url

    def __repr__(self):
        return "<Experiment: %s version:%s>" % (self.name, self.newrlms)

    def __unicode__(self):
        return "%s @ %s" % (self.name, self.newrlms)

    @classmethod
    def find_with_id_and_rlms_id(self, id, rlms_id):
        return DBS.query(self).filter(sql.and_(self.id == id, self.rlms_id == rlms_id)).first()

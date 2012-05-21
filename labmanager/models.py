from sqlalchemy import Column, Integer, String
from labmanager.database import Base

class LMS(Base):

    __tablename__ = 'lmss'

    id = Column(Integer, primary_key=True)

    name     = Column(String(50),  unique=True)
    # Hash
    password = Column(String(50))

    def __init__(self, name = None, password = None):
        self.name     = name
        self.password = password

    def __repr__(self):
        return 'User(%r)' % self.name



from sqlalchemy import Column, Integer, String
from labmanager.database import Base

class User(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)

    name     = Column(String(50),  unique=True)
    email    = Column(String(120))

    # Hash
    password = Column(String(50))

    def __init__(self, name = None, email = None, password = None):
        self.name     = name
        self.email    = email
        self.password = password

    def __repr__(self):
        return 'User(%r)' % self.name



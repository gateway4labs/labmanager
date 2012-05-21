#-*-*- encoding: utf-8 -*-*-
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from config import SQLALCHEMY_ENGINE_STR

try:
    from config import USE_PYMYSQL
except ImportError:
    USE_PYMYSQL = False

if USE_PYMYSQL:
    import pymysql_sa
    pymysql_sa.make_default_mysql_dialect()

engine = create_engine(SQLALCHEMY_ENGINE_STR, convert_unicode=True)

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db(drop = False):
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import labmanager.models
    if drop:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def add_sample_users():
    from labmanager.models import LMS

    init_db(drop = True)
    password = hashlib.new("sha", "password").hexdigest()
    lms1 = LMS("uned",   "Universidad Nacional de Educación a Distancia", password)
    lms2 = LMS("deusto", "Universidad de Deusto", password)
    db_session.add(lms1)
    db_session.add(lms2)
    db_session.commit()


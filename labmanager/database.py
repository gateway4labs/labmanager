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
    from labmanager.models import LMS, LabManagerUser, RLMSType, RLMSTypeVersion, RLMS, Course

    init_db(drop = True)
    password = hashlib.new('sha', 'password').hexdigest()

    lms1 = LMS('Universidad Nacional de Educación a Distancia', "http://localhost:5000/fake_list_courses", 'uned', password, "labmanager", "password")
    lms2 = LMS('Universidad de Deusto', "http://localhost:5000/fake_list_courses", 'deusto', password, "labmanager", "password")

    course1 = Course(lms1, "5", "my course 1")
    course2 = Course(lms2, "6", "my course 2")

    user1 = LabManagerUser('porduna', 'Pablo Orduña', password)
    user2 = LabManagerUser('elio', 'Elio Sancristobal', password)

    db_session.add(lms1)
    db_session.add(lms2)

    db_session.add(course1)
    db_session.add(course2)

    db_session.add(user1)
    db_session.add(user2)

    weblab_deusto = RLMSType('WebLab-Deusto')
    ilab          = RLMSType('iLab')
    unsupported   = RLMSType('Unsupported')

    weblab_deusto_4_0 = RLMSTypeVersion(weblab_deusto, '4.0')
    weblab_deusto_4_5 = RLMSTypeVersion(weblab_deusto, '4.5')
    unsupported_4_5 = RLMSTypeVersion(unsupported,   '4.5')

    ilab_4_0 = RLMSTypeVersion(ilab, '4.5')

    weblab_deusto_instance = RLMS(name = "WebLab-Deusto at Deusto", location = "Deusto", rlms_version = weblab_deusto_4_0, configuration = "{}")

    ilab_instance          = RLMS(name = "iLab MIT",                location = "MIT",    rlms_version = ilab_4_0, configuration = "{}")

    db_session.add(weblab_deusto)
    db_session.add(ilab)
    db_session.add(weblab_deusto_4_0)
    db_session.add(weblab_deusto_4_5)
    db_session.add(unsupported_4_5)
    db_session.add(ilab_4_0)
    db_session.add(weblab_deusto_instance)
    db_session.add(ilab_instance)

    db_session.commit()


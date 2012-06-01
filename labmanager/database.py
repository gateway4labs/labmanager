#-*-*- encoding: utf-8 -*-*-
import json
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
    from labmanager.models import LMS, LabManagerUser, RLMSType, RLMSTypeVersion, RLMS, Course, PermissionOnCourse, PermissionOnLaboratory, Laboratory

    init_db(drop = True)
    password = unicode(hashlib.new('sha', 'password').hexdigest())

    lms1 = LMS(u'Universidad Nacional de Educacion a Distancia', u"http://localhost:5000/fake_list_courses", u'uned', password, u"labmanager", u"password")
    lms2 = LMS(u'Universidad de Deusto', u"http://localhost:5000/fake_list_courses", u'deusto', password, u"labmanager", u"password")

    course1 = Course(lms1, u"1", u"my course 1")
    course2 = Course(lms2, u"2", u"my course 2")

    user1 = LabManagerUser(u'porduna', u'Pablo Orduna', password)
    user2 = LabManagerUser(u'elio', u'Elio Sancristobal', password)
    user3 = LabManagerUser(u'apm', u'Alberto Pesquera Martin', password)

    db_session.add(lms1)
    db_session.add(lms2)

    db_session.add(course1)
    db_session.add(course2)

    db_session.add(user1)
    db_session.add(user2)
    db_session.add(user3)

    weblab_deusto = RLMSType(u'WebLab-Deusto')
    ilab          = RLMSType(u'iLab')
    unsupported   = RLMSType(u'Unsupported')

    weblab_deusto_4_0 = RLMSTypeVersion(weblab_deusto, u'4.0')
    weblab_deusto_4_5 = RLMSTypeVersion(weblab_deusto, u'4.5')
    unsupported_4_5 = RLMSTypeVersion(unsupported,   u'4.5')

    ilab_4_0 = RLMSTypeVersion(ilab, u'4.5')
   
    configuration = {
        'remote_login' : 'weblabfed',
        'password'     : 'password',
        'base_url'     : 'http://www.weblab.deusto.es/weblab/',
    }

    weblab_deusto_instance = RLMS(name = u"WebLab-Deusto at Deusto", location = u"Deusto", rlms_version = weblab_deusto_4_0, configuration = unicode(json.dumps(configuration)))

    ilab_instance          = RLMS(name = u"iLab MIT",                location = u"MIT",    rlms_version = ilab_4_0, configuration = u"{}")

    db_session.add(weblab_deusto)
    db_session.add(ilab)
    db_session.add(weblab_deusto_4_0)
    db_session.add(weblab_deusto_4_5)
    db_session.add(unsupported_4_5)
    db_session.add(ilab_4_0)
    db_session.add(weblab_deusto_instance)
    db_session.add(ilab_instance)

    robot_lab = Laboratory(name = u"robot-movement@Robot experiments", laboratory_id = u"robot-movement@Robot experiments", rlms = weblab_deusto_instance)

    permission_on_uned   = PermissionOnLaboratory(lms = lms1, laboratory = robot_lab, configuration = u"{}", local_identifier = u"robot")
    permission_on_deusto = PermissionOnLaboratory(lms = lms2, laboratory = robot_lab, configuration = u"{}", local_identifier = u"robot")

    db_session.add(permission_on_uned)
    db_session.add(permission_on_deusto)

    permission_on_course1 = PermissionOnCourse(permission_on_lab = permission_on_uned,   course = course1, configuration = u"{}")
    permission_on_course2 = PermissionOnCourse(permission_on_lab = permission_on_deusto, course = course2, configuration = u"{}")

    db_session.add(permission_on_course1)
    db_session.add(permission_on_course2)

    db_session.commit()


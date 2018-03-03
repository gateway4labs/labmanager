# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import os
import hashlib

from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, MetaData

from flask.ext.sqlalchemy import SQLAlchemy

from labmanager import ALGORITHM
from labmanager.utils import data_filename
from labmanager.application import app

if app.config.get('USE_PYMYSQL', False):
    import pymysql_sa
    pymysql_sa.make_default_mysql_dialect()

db = SQLAlchemy()
db.init_app(app)

db_session = db.session

Base = db.Model

def create_alembic_config(silence = False):
    if silence:
        alembic_config = Config("alembic_test.ini")
    else:
        alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("script_location", os.path.abspath(data_filename('alembic')))
    alembic_config.set_main_option("url", app.config['SQLALCHEMY_DATABASE_URI'])
    alembic_config.set_main_option("sqlalchemy.url", app.config['SQLALCHEMY_DATABASE_URI'])
    return alembic_config

def init_db(drop = False, silence = False):
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from labmanager.models import LabManagerUser

    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

    if drop:
        print "Droping Database"
        Base.metadata.drop_all(bind=engine)
        meta = MetaData(engine)
        meta.reflect()
        if 'alembic_version' in meta.tables:
            meta.drop_all()

    alembic_config = create_alembic_config(silence)

    alembic_config.set_section_option('logger_alembic', 'level', 'WARN')

    with app.app_context():
        db.create_all()

    command.stamp(alembic_config, "head")

    with app.app_context():
        password = unicode(hashlib.new(ALGORITHM, 'password').hexdigest())
        admin_user = LabManagerUser(u'admin', u'Administrator', password)

        db.session.add(admin_user)
        db.session.commit()

def check_version():
    alembic_config = create_alembic_config()
    script = ScriptDirectory.from_config(alembic_config)
    head = script.get_current_head()

    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

    context = MigrationContext.configure(engine)
    current_rev = context.get_current_revision()

    return head == current_rev


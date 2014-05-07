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
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import SQLALCHEMY_ENGINE_STR, USE_PYMYSQL

if USE_PYMYSQL:
    import pymysql_sa
    pymysql_sa.make_default_mysql_dialect()

engine = create_engine(SQLALCHEMY_ENGINE_STR, convert_unicode=True, pool_recycle=3600)

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

alembic_config = Config("alembic.ini")
alembic_config.set_main_option("script_location", os.path.abspath('alembic'))
alembic_config.set_main_option("url", SQLALCHEMY_ENGINE_STR)
alembic_config.set_main_option("sqlalchemy.url", SQLALCHEMY_ENGINE_STR)

def init_db(drop = False):
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from labmanager.models import LabManagerUser

    if drop:
        print "Droping Database"
        Base.metadata.drop_all(bind=engine)
        meta = MetaData(engine)
        meta.reflect()
        if 'alembic_version' in meta.tables:
            meta.drop_all()

    command.upgrade(alembic_config, "head")

    password = unicode(hashlib.new('sha', 'password').hexdigest())
    admin_user = LabManagerUser(u'admin', u'Administrator', password)
    db_session.add(admin_user)
    db_session.commit()

def check_version():
    script = ScriptDirectory.from_config(alembic_config)
    head = script.get_current_head()

    engine = create_engine(SQLALCHEMY_ENGINE_STR)

    context = MigrationContext.configure(engine)
    current_rev = context.get_current_revision()

    return head == current_rev


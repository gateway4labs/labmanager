"""Populate RLMS name

Revision ID: e657e849733
Revises: 298c12227419
Create Date: 2015-05-10 19:56:50.353550

"""

# revision identifiers, used by Alembic.
revision = 'e657e849733'
down_revision = '298c12227419'

from alembic import op
import sqlalchemy as sa
import sqlalchemy.sql as sql

from labmanager.db import db
from labmanager.application import app

metadata = db.MetaData()
rlms = db.Table('rlmss', metadata,
    db.Column('id', db.Integer()),
    db.Column('name', db.Unicode(50)),
    db.Column('kind', db.Unicode(50)),
    db.Column('version', db.Unicode(50)),
    db.Column('configuration', db.Unicode(10 * 1024)),
)

def upgrade():
    with app.app_context():
        for id, name, kind, version, configuration in db.session.execute(sql.select([rlms.c.id, rlms.c.name, rlms.c.kind, rlms.c.version, rlms.c.configuration])):
            kwargs = {}
            if not name:
                kwargs['name'] = u'%s - %s' % (kind, version)

            if kind == 'Virtual labs':
                config = json.loads(configuration)
                if 'name' in config and 'web_name' not in config:
                    config['web_name'] = config.pop('name')
                    kwargs['configuration'] = json.dumps(config)

            if kwargs:
                update_stmt = rlms.update().where(rlms.c.id == id).values(**kwargs)
                db.session.execute(update_stmt)

        db.session.commit()



def downgrade():
    pass

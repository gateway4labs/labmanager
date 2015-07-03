"""Resize fields

Revision ID: f2b0984f780
Revises: 37e42fa9d88e
Create Date: 2015-07-03 12:35:58.448260

"""

# revision identifiers, used by Alembic.
revision = 'f2b0984f780'
down_revision = '37e42fa9d88e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column("rlmss", "name", type_ = sa.Unicode(255))
    op.alter_column("rlmss", "location", type_ = sa.Unicode(255))


def downgrade():
    pass


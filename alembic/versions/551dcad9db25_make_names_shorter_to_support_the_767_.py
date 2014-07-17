"""Make names shorter to support the 767 limit of MySQL

Revision ID: 551dcad9db25
Revises: 3ee46f95bcce
Create Date: 2014-07-17 19:00:20.564865

"""

# revision identifiers, used by Alembic.
revision = '551dcad9db25'
down_revision = '3ee46f95bcce'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column("laboratories", "laboratory_id", type_ = sa.Unicode(255))
    op.alter_column("laboratories", "name", type_ = sa.Unicode(255))

def downgrade():
    pass

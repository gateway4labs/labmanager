"""Make Laboratory name longer

Revision ID: 3ee46f95bcce
Revises: 4bc4c1ae0f38
Create Date: 2014-04-29 21:29:43.714010

"""

# revision identifiers, used by Alembic.
revision = '3ee46f95bcce'
down_revision = '4bc4c1ae0f38'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column("laboratories", "laboratory_id", type_ = sa.Unicode(350))
    op.alter_column("laboratories", "name", type_ = sa.Unicode(350))


def downgrade():
    op.alter_column("laboratories", "laboratory_id", type_ = sa.Unicode(50))
    op.alter_column("laboratories", "name", type_ = sa.Unicode(50))

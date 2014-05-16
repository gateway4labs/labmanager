"""Validation and completion of HTTP RLMS

Revision ID: 33058c41765c
Revises: 3ee46f95bcce
Create Date: 2014-05-16 10:00:23.411755

"""

# revision identifiers, used by Alembic.
revision = '33058c41765c'
down_revision = '3ee46f95bcce'

from alembic import op
import sqlalchemy as sa


def upgrade():    

    op.add_column('rlmss', sa.Column('validated', sa.Boolean(), nullable=False))
    op.add_column('rlmss', sa.Column('newrlms', sa.Boolean(), nullable=False))

    op.create_table('http_rlms_property',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('rlms_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Unicode(length=50), nullable=False),
    sa.Column('value', sa.Unicode(length=50), nullable=False),
    sa.ForeignKeyConstraint(['rlms_id'], ['rlmss.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name','rlms_id')
    )

def downgrade():
    op.drop_column('rlmss', 'validated')
    op.drop_column('rlmss', 'newrlms')

    op.drop_table('http_rlms_property')

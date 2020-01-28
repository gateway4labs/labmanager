"""Anonymize ip addresses

Revision ID: 414d69d7ee76
Revises: 58abc4899824
Create Date: 2020-01-27 20:54:54.304630

"""

# revision identifiers, used by Alembic.
revision = '414d69d7ee76'
down_revision = '58abc4899824'

import ipaddress

from alembic import op
import sqlalchemy as sa
import sqlalchemy.sql as sql

metadata = sa.MetaData()
use_logs = sa.Table('UseLogs', metadata,
    sa.Column('id', sa.Integer()),
    sa.Column('ip_address', sa.Unicode(100)),
)

def anonymize_ip_address(ip_address):
    if not ip_address:
        return ip_address

    potential_ip_addresses = []

    for potential_ip_address in ip_address.split(','):
        potential_ip_address = potential_ip_address.strip()
        if not isinstance(potential_ip_address, unicode):
            potential_ip_address = potential_ip_address.decode()

        try:
            complete_ip_address = ipaddress.ip_address(potential_ip_address)
        except:
            # Error parsing potential_origin
            continue

        # Remove 80 bits or 8 bits, depending on the version
        if complete_ip_address.version == 6:
            bytes_removed = 10
        elif complete_ip_address.version == 4:
            bytes_removed = 1
        else:
            raise Exception("IP version {} not supported: {}".format(complete_ip_address.version, potential_ip_address))

        anonymized_packed = complete_ip_address.packed[:-bytes_removed] + (b'\x00' * bytes_removed)
        anonymized_ip_address = ipaddress.ip_address(anonymized_packed)
        potential_ip_addresses.append(anonymized_ip_address.compressed)

    return ', '.join(potential_ip_addresses)

def upgrade():
    for use_row in op.get_bind().execute(sql.select([use_logs.c.id, use_logs.c.ip_address])):
        use_id = use_row[use_logs.c.id]
        ip_address = use_row[use_logs.c.ip_address]
        new_ip_address = anonymize_ip_address(ip_address)

        stmt = use_logs.update().where(use_logs.c.id == use_id).values(ip_address=new_ip_address)
        op.execute(stmt)

def downgrade():
    pass

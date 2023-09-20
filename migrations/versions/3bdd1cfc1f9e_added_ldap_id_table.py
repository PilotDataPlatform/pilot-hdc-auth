# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""Added ldap id table.

Revision ID: 3bdd1cfc1f9e
Revises: c50577f5d93e
Create Date: 2022-08-31 09:26:28.984287
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '3bdd1cfc1f9e'
down_revision = 'c50577f5d93e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'ldap_id',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
        schema='pilot_ldap',
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ldap_id', schema='pilot_ldap')
    # ### end Alembic commands ###

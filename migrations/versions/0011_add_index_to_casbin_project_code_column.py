# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""Add index to casbin project code column.

Revision ID: 0011
Revises: 0010
Create Date: 2023-03-30 18:58:17.372474
"""
from alembic import op

revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = '0010'


def upgrade():
    op.create_index(op.f('ix_pilot_casbin_casbin_rule_v4'), 'casbin_rule', ['v4'], unique=False, schema='pilot_casbin')


def downgrade():
    op.drop_index(op.f('ix_pilot_casbin_casbin_rule_v4'), table_name='casbin_rule', schema='pilot_casbin')

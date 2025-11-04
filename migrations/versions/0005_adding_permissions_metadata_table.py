# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Populating permissions metadata.

Revision ID: 0006
Revises: 0005
Create Date: 2023-02-22 09:51:47.395622
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '3bdd1cfc1f9e'
branch_labels = None
depends_on = '3bdd1cfc1f9e'


def upgrade():
    op.create_table(
        'permission_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('tooltip', sa.String(), nullable=True),
        sa.Column('resource', sa.String(), nullable=True),
        sa.Column('operation', sa.String(), nullable=True),
        sa.Column('zone', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
        sa.UniqueConstraint('resource', 'operation', 'zone', name='resource_operation_zone_unique'),
        schema='public',
    )


def downgrade():
    op.drop_table('permission_metadata', schema='public')

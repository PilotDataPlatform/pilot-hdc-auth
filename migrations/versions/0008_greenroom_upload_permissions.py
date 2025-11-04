# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Greenroom Upload permissions.

Revision ID: 0008
Revises: 0007
Create Date: 2023-03-17 15:15:10.990758
"""
from alembic import op
from sqlalchemy import MetaData
from sqlalchemy import Table

# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = '0007'


def upgrade():
    meta = MetaData(bind=op.get_bind())
    meta.reflect(only=('permission_metadata',))
    permission_metadata_table = Table('permission_metadata', meta)
    op.execute(
        permission_metadata_table.update()
        .where(permission_metadata_table.c.resource == 'file_any')
        .where(permission_metadata_table.c.operation == 'upload')
        .where(permission_metadata_table.c.zone == 'core')
        .values(name='Upload Data (to all namefolders) in Core')
    )


def downgrade():
    meta = MetaData(bind=op.get_bind())
    meta.reflect(only=('permission_metadata',))
    permission_metadata_table = Table('permission_metadata', meta)
    op.execute(
        permission_metadata_table.update()
        .where(permission_metadata_table.c.resource == 'file_any')
        .where(permission_metadata_table.c.operation == 'upload')
        .where(permission_metadata_table.c.zone == 'core')
        .values(name='Upload Data (to own namefolder) in Green Room')
    )

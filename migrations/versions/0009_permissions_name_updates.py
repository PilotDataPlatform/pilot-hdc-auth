# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from alembic import op
from sqlalchemy import MetaData
from sqlalchemy import Table

# revision identifiers, used by Alembic.
revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = '0008'


def upgrade():
    meta = MetaData(bind=op.get_bind())
    meta.reflect(only=('permission_metadata',))
    permission_metadata_table = Table('permission_metadata', meta)
    op.execute(
        permission_metadata_table.update()
        .where(permission_metadata_table.c.resource == 'file_in_own_namefolder')
        .where(permission_metadata_table.c.operation == 'download')
        .where(permission_metadata_table.c.zone == 'core')
        .values(name='Download Data (from own namefolder) in Core')
    )
    op.execute(
        permission_metadata_table.update()
        .where(permission_metadata_table.c.resource == 'file_any')
        .where(permission_metadata_table.c.operation == 'view')
        .where(permission_metadata_table.c.zone == 'greenroom')
        .values(name='View (all) Data in Green Room')
    )
    op.execute(
        permission_metadata_table.update()
        .where(permission_metadata_table.c.resource == 'file_any')
        .where(permission_metadata_table.c.operation == 'view')
        .where(permission_metadata_table.c.zone == 'core')
        .values(name='View (all) Data in Core')
    )


def downgrade():
    meta = MetaData(bind=op.get_bind())
    meta.reflect(only=('permission_metadata',))
    permission_metadata_table = Table('permission_metadata', meta)
    op.execute(
        permission_metadata_table.update()
        .where(permission_metadata_table.c.resource == 'file_in_own_namefolder')
        .where(permission_metadata_table.c.operation == 'download')
        .where(permission_metadata_table.c.zone == 'core')
        .values(name='Download Data (from all namefolders) in Core')
    )
    op.execute(
        permission_metadata_table.update()
        .where(permission_metadata_table.c.resource == 'file_any')
        .where(permission_metadata_table.c.operation == 'view')
        .where(permission_metadata_table.c.zone == 'greenroom')
        .values(name='View (others) Data in Green Room')
    )
    op.execute(
        permission_metadata_table.update()
        .where(permission_metadata_table.c.resource == 'file_any')
        .where(permission_metadata_table.c.operation == 'view')
        .where(permission_metadata_table.c.zone == 'core')
        .values(name='View (others) Data in Core')
    )

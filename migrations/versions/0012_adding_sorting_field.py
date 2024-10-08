# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""adding sorting field.

Revision ID: 0012
Revises: 0011
Create Date: 2023-03-30 12:21:25.471047
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import MetaData
from sqlalchemy import Table

# revision identifiers, used by Alembic.
revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = '0011'

METADATA = [
    {
        'name': 'View (own) Data in Green Room',
        'sorting_position': 10,
    },
    {
        'name': 'View (all) Data in Green Room',
        'sorting_position': 20,
    },
    {
        'name': 'Upload Data (to own namefolder) in Green Room',
        'new_name': 'Upload Data (to own folder) in Green Room',
        'sorting_position': 30,
    },
    {
        'name': 'Upload Data (to all namefolders) in Green Room',
        'new_name': 'Upload Data (to all folders) in Green Room',
        'sorting_position': 40,
    },
    {
        'name': 'Annotate Data (in own namefolder) in Green Room',
        'new_name': 'Annotate Data (in own folder) in Green Room',
        'sorting_position': 50,
    },
    {
        'name': 'Annotate Data (in any namefolder) in Green Room',
        'new_name': 'Annotate Data (in all folders) in Green Room',
        'sorting_position': 60,
    },
    {
        'name': 'Download Data (from own namefolder) in Green Room',
        'new_name': 'Download Data (from own folder) in Green Room',
        'sorting_position': 70,
    },
    {
        'name': 'Download Data (from all namefolders) in Green Room',
        'new_name': 'Download Data (from all folders) in Green Room',
        'sorting_position': 80,
    },
    {
        'name': 'Delete Data (from own namefolder) in Green Room',
        'new_name': 'Delete Data (from own folder) in Green Room',
        'sorting_position': 90,
    },
    {
        'name': 'Delete Data (from all namefolders) in Green Room',
        'new_name': 'Delete Data (from all folders) in Green Room',
        'sorting_position': 100,
    },
    {
        'name': 'Copy Data (in own namefolder) from Green Room to Core',
        'new_name': 'Copy Data (in own folder) from Green Room to Core',
        'sorting_position': 110,
    },
    {
        'name': 'Copy Data (in all namefolders) from Green Room to Core',
        'new_name': 'Copy Data (in all folders) from Green Room to Core',
        'sorting_position': 120,
    },
    {
        'name': 'Create Data copy request (from own namefolder) in Green Room',
        'new_name': 'Request Data copy (from own folder) in Green Room',
        'sorting_position': 130,
    },
    {
        'name': 'Create Data copy request (from all namefolders) in Green Room',
        'new_name': 'Request Data copy (from all folders) in Green Room',
        'sorting_position': 140,
    },
    {
        'name': 'View (own) Data in Core',
        'sorting_position': 150,
    },
    {
        'name': 'View (all) Data in Core',
        'sorting_position': 160,
    },
    {
        'name': 'Upload Data (to own namefolder) in Core',
        'new_name': 'Upload Data (to own folder) in Core',
        'sorting_position': 170,
    },
    {
        'name': 'Upload Data (to all namefolders) in Core',
        'new_name': 'Upload Data (to all folders) in Core',
        'sorting_position': 180,
    },
    {
        'name': 'Annotate Data (in own namefolder) in Core',
        'new_name': 'Annotate Data (in own folder) in Core',
        'sorting_position': 190,
    },
    {
        'name': 'Annotate Data (in any namefolder) in Core',
        'new_name': 'Annotate Data (in all folders) in Core',
        'sorting_position': 200,
    },
    {
        'name': 'Download Data (from own namefolder) in Core',
        'new_name': 'Download Data (from own folder) in Core',
        'sorting_position': 210,
    },
    {
        'name': 'Download Data (from all namefolders) in Core',
        'new_name': 'Download Data (from all folders) in Core',
        'sorting_position': 220,
    },
    {
        'name': 'Delete Data (from own namefolder) in Core',
        'new_name': 'Delete Data (from own folder) in Core',
        'sorting_position': 230,
    },
    {
        'name': 'Delete Data (from all namefolders) in Core',
        'new_name': 'Delete Data (from all folders) in Core',
        'sorting_position': 240,
    },
]


def upgrade():
    op.add_column('permission_metadata', sa.Column('sorting_position', sa.Integer(), nullable=True))

    meta = MetaData(bind=op.get_bind())
    meta.reflect(only=('permission_metadata',))
    permission_metadata_table = Table('permission_metadata', meta)
    for item in METADATA:
        if item.get('new_name'):
            op.execute(
                permission_metadata_table.update()
                .where(permission_metadata_table.c.name == item['name'])
                .values(name=item['new_name'], sorting_position=item['sorting_position'])
            )
        else:
            op.execute(
                permission_metadata_table.update()
                .where(permission_metadata_table.c.name == item['name'])
                .values(sorting_position=item['sorting_position'])
            )


def downgrade():
    op.drop_column('permission_metadata', 'sorting_position')

    meta = MetaData(bind=op.get_bind())
    meta.reflect(only=('permission_metadata',))
    permission_metadata_table = Table('permission_metadata', meta)
    for item in METADATA:
        if item.get('new_name'):
            op.execute(
                permission_metadata_table.update()
                .where(permission_metadata_table.c.name == item['new_name'])
                .values(name=item['name'])
            )

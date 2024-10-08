# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""Updating copy permission.

Revision ID: 0007
Revises: 0006
Create Date: 2023-03-08 10:07:52.259321
"""
from uuid import uuid4

from alembic import op
from sqlalchemy import MetaData
from sqlalchemy import Table

# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = '0006'


PERMISSION_DATA = [
    {
        'id': str(uuid4()),
        'name': 'Copy Data (in own namefolder) from Green Room to Core',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_in_own_namefolder',
        'operation': 'copy',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'Copy Data (in all namefolders) from Green Room to Core',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_any',
        'operation': 'copy',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'Create Data copy request (from own namefolder) in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'copyrequest_in_own_namefolder',
        'operation': 'create',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'Create Data copy request (from all namefolders) in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'copyrequest_in_any_namefolder',
        'operation': 'create',
        'zone': 'greenroom',
    },
]


def upgrade():
    meta = MetaData(bind=op.get_bind())
    meta.reflect(only=('permission_metadata',))
    permission_metadata_table = Table('permission_metadata', meta)

    op.execute(
        permission_metadata_table.delete()
        .where(permission_metadata_table.c.resource.in_(['file_any', 'file_in_own_namefolder']))
        .where(permission_metadata_table.c.operation == 'copy')
    )

    op.execute(
        permission_metadata_table.delete()
        .where(permission_metadata_table.c.resource == 'copyrequest')
        .where(permission_metadata_table.c.operation == 'create')
    )

    op.bulk_insert(permission_metadata_table, PERMISSION_DATA)


def downgrade():
    meta = MetaData(bind=op.get_bind())
    meta.reflect(only=('permission_metadata',))
    permission_metadata_table = Table('permission_metadata', meta)
    for permission in PERMISSION_DATA:
        op.execute(
            permission_metadata_table.delete()
            .where(permission_metadata_table.c.resource == permission['resource'])
            .where(permission_metadata_table.c.operation == permission['operation'])
        )

    PREVIOUS_DATA = [
        {
            'id': str(uuid4()),
            'name': 'Copy Data (in own namefolder) from Green Room to Core',
            'category': 'Data Operation Permissions',
            'tooltip': '',
            'resource': 'file_in_own_namefolder',
            'operation': 'copy',
            'zone': '*',
        },
        {
            'id': str(uuid4()),
            'name': 'Copy Data (in all namefolders) from Green Room to Core',
            'category': 'Data Operation Permissions',
            'tooltip': '',
            'resource': 'file_any',
            'operation': 'copy',
            'zone': '*',
        },
        {
            'id': str(uuid4()),
            'name': 'Create Data copy request (from own namefolder) in Green Room',
            'category': 'Data Operation Permissions',
            'tooltip': '',
            'resource': 'file_in_own_namefolder',
            'operation': 'copy',
            'zone': 'greenroom',
        },
        {
            'id': str(uuid4()),
            'name': 'Create Data copy request (from own namefolder) in Core',
            'category': 'Data Operation Permissions',
            'tooltip': '',
            'resource': 'file_in_own_namefolder',
            'operation': 'copy',
            'zone': 'core',
        },
        {
            'id': str(uuid4()),
            'name': 'Create Data copy request (from all namefolders) in Green Room',
            'category': 'Data Operation Permissions',
            'tooltip': '',
            'resource': 'file_any',
            'operation': 'copy',
            'zone': 'greenroom',
        },
        {
            'id': str(uuid4()),
            'name': 'Create Data copy request (from all namefolders) in Core',
            'category': 'Data Operation Permissions',
            'tooltip': '',
            'resource': 'file_any',
            'operation': 'copy',
            'zone': 'core',
        },
    ]
    op.bulk_insert(permission_metadata_table, PREVIOUS_DATA)

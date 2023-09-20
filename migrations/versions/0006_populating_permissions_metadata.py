# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""Populating permissions metadata.

Revision ID: 0006
Revises: 0005
Create Date: 2023-02-22 09:51:47.395622
"""
from uuid import uuid4

from alembic import op
from sqlalchemy import MetaData
from sqlalchemy import Table

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = '0005'


PERMISSION_DATA = [
    {
        'id': str(uuid4()),
        'name': 'View (others) Data in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_any',
        'operation': 'view',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'View (others) Data in Core',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_any',
        'operation': 'view',
        'zone': 'core',
    },
    {
        'id': str(uuid4()),
        'name': 'View (own) Data in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_in_own_namefolder',
        'operation': 'view',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'View (own) Data in Core',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_in_own_namefolder',
        'operation': 'view',
        'zone': 'core',
    },
    {
        'id': str(uuid4()),
        'name': 'Upload Data (to own namefolder) in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_in_own_namefolder',
        'operation': 'upload',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'Upload Data (to all namefolders) in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_any',
        'operation': 'upload',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'Upload Data (to own namefolder) in Core',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_in_own_namefolder',
        'operation': 'upload',
        'zone': 'core',
    },
    {
        'id': str(uuid4()),
        'name': 'Upload Data (to own namefolder) in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_any',
        'operation': 'upload',
        'zone': 'core',
    },
    {
        'id': str(uuid4()),
        'name': 'Download Data (from all namefolders) in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_any',
        'operation': 'download',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'Download Data (from own namefolder) in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_in_own_namefolder',
        'operation': 'download',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'Download Data (from all namefolders) in Core',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_any',
        'operation': 'download',
        'zone': 'core',
    },
    {
        'id': str(uuid4()),
        'name': 'Download Data (from all namefolders) in Core',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_in_own_namefolder',
        'operation': 'download',
        'zone': 'core',
    },
    {
        'id': str(uuid4()),
        'name': 'Delete Data (from all namefolders) in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_any',
        'operation': 'delete',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'Delete Data (from all namefolders) in Core',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_any',
        'operation': 'delete',
        'zone': 'core',
    },
    {
        'id': str(uuid4()),
        'name': 'Delete Data (from own namefolder) in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_in_own_namefolder',
        'operation': 'delete',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'Delete Data (from own namefolder) in Core',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_in_own_namefolder',
        'operation': 'delete',
        'zone': 'core',
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
    {
        'id': str(uuid4()),
        'name': 'Annotate Data (in own namefolder) in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_in_own_namefolder',
        'operation': 'annotate',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'Annotate Data (in own namefolder) in Core',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_in_own_namefolder',
        'operation': 'annotate',
        'zone': 'core',
    },
    {
        'id': str(uuid4()),
        'name': 'Annotate Data (in any namefolder) in Green Room',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_any',
        'operation': 'annotate',
        'zone': 'greenroom',
    },
    {
        'id': str(uuid4()),
        'name': 'Annotate Data (in any namefolder) in Core',
        'category': 'Data Operation Permissions',
        'tooltip': '',
        'resource': 'file_any',
        'operation': 'annotate',
        'zone': 'core',
    },
    {
        'id': str(uuid4()),
        'name': 'Create Project Announcement',
        'category': 'Announcement',
        'tooltip': '',
        'resource': 'announcement',
        'operation': 'create',
        'zone': '*',
    },
    {
        'id': str(uuid4()),
        'name': 'Send Resource Request',
        'category': 'Workbench',
        'tooltip': '',
        'resource': 'resource_request',
        'operation': 'create',
        'zone': '*',
    },
    {
        'id': str(uuid4()),
        'name': 'Manage Resource Requests',
        'category': 'Workbench',
        'tooltip': '',
        'resource': 'resource_request',
        'operation': 'manage',
        'zone': '*',
    },
    {
        'id': str(uuid4()),
        'name': 'Workbench Manage',
        'category': 'Workbench',
        'tooltip': '',
        'resource': 'workbench',
        'operation': 'manage',
        'zone': '*',
    },
    {
        'id': str(uuid4()),
        'name': 'Manage Users',
        'category': 'Users',
        'tooltip': '',
        'resource': 'users',
        'operation': 'manage',
        'zone': '*',
    },
    {
        'id': str(uuid4()),
        'name': 'View users in Project',
        'category': 'Users',
        'tooltip': '',
        'resource': 'users',
        'operation': 'view',
        'zone': '*',
    },
    {
        'id': str(uuid4()),
        'name': 'Approve Copy Requests',
        'category': 'Users',
        'tooltip': '',
        'resource': 'copyrequest',
        'operation': 'manage',
        'zone': '*',
    },
    {
        'id': str(uuid4()),
        'name': 'Project Information Update',
        'category': 'Users',
        'tooltip': '',
        'resource': 'project',
        'operation': 'update',
        'zone': '*',
    },
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
]


def upgrade():
    meta = MetaData(bind=op.get_bind())
    meta.reflect(only=('permission_metadata',))
    permission_metadata_table = Table('permission_metadata', meta)
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

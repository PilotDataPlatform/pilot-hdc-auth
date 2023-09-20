# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""Adding role table.

Revision ID: 0008
Revises: 0007
Create Date: 2023-03-16 13:27:38.430290
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = '0009'


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'role',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('project_code', sa.String(), nullable=True),
        sa.Column('time_created', sa.DateTime(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('role')
    # ### end Alembic commands ###

# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from app.config import ConfigSettings

Base = declarative_base()


def expiry_time():
    return datetime.utcnow() + timedelta(minutes=ConfigSettings.INVITE_EXPIRY_MINUTES)


class InvitationModel(Base):
    __tablename__ = 'invitation'
    __table_args__ = {'schema': ConfigSettings.RDS_SCHEMA_PREFIX + '_invitation'}
    id = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid4)
    invitation_code = Column(UUID(as_uuid=True), unique=True, default=uuid4)
    expiry_timestamp = Column(DateTime(), default=expiry_time)
    create_timestamp = Column(DateTime(), default=datetime.utcnow)
    invited_by = Column(String())
    email = Column(String())
    platform_role = Column(String())
    project_role = Column(String())
    project_code = Column(String())
    status = Column(String())

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        result = {}
        field_list = [
            'id',
            'invitation_code',
            'expiry_timestamp',
            'create_timestamp',
            'invited_by',
            'email',
            'platform_role',
            'project_role',
            'project_code',
            'status',
        ]
        for field in field_list:
            if getattr(self, field):
                result[field] = str(getattr(self, field))
            else:
                result[field] = ''
        return result

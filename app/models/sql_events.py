# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from app.config import ConfigSettings

Base = declarative_base()


class UserEventModel(Base):
    __tablename__ = 'user_event'
    __table_args__ = {'schema': ConfigSettings.RDS_SCHEMA_PREFIX + '_event'}
    id = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid4)
    target_user_id = Column(UUID(as_uuid=True))
    target_user = Column(String())
    operator_id = Column(UUID(as_uuid=True), nullable=True)
    operator = Column(String())
    event_type = Column(String())
    timestamp = Column(DateTime(), default=datetime.utcnow)
    detail = Column(JSON())

    def to_dict(self):
        result = {}
        field_list = [
            'id',
            'target_user',
            'target_user_id',
            'operator',
            'operator_id',
            'event_type',
            'timestamp',
            'detail',
        ]
        for field in field_list:
            if field != 'detail':
                if getattr(self, field):
                    result[field] = str(getattr(self, field))
                else:
                    result[field] = ''
            else:
                if not self.detail:
                    result['detail'] = {}
                else:
                    result[field] = getattr(self, field)
        return result

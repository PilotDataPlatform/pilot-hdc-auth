# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from app.config import ConfigSettings

Base = declarative_base()


class CasbinRule(Base):
    __tablename__ = 'casbin_rule'
    __table_args__ = {'schema': ConfigSettings.RDS_SCHEMA_PREFIX + '_casbin'}

    id = Column(Integer, primary_key=True)
    ptype = Column(String(255))
    v0 = Column(String(255))
    v1 = Column(String(255))
    v2 = Column(String(255))
    v3 = Column(String(255))
    v4 = Column(String(255), index=True)
    v5 = Column(String(255))

    def __str__(self):
        arr = [self.ptype]
        for v in (self.v0, self.v1, self.v2, self.v3, self.v4, self.v5):
            if v is None:
                break
            arr.append(v)
        return ', '.join(arr)

    def __repr__(self):
        return f'<CasbinRule {self.id}: "{self}">'


class PermissionMetadataModel(Base):
    __tablename__ = 'permission_metadata'
    __table_args__ = (UniqueConstraint('resource', 'operation', name='resource_operation_unique'),)

    id = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid4)
    name = Column(String())
    category = Column(String())
    tooltip = Column(String(), default='')
    resource = Column(String())
    operation = Column(String())
    zone = Column(String())
    sorting_position = Column(Integer())

    def to_dict(self):
        result = {}
        field_list = [
            'id',
            'name',
            'category',
            'tooltip',
            'resource',
            'operation',
            'zone',
            'sorting_position',
        ]
        for field in field_list:
            if getattr(self, field):
                if field != 'sorting_position':
                    result[field] = str(getattr(self, field))
                else:
                    result[field] = getattr(self, field)
            else:
                result[field] = ''
        return result


class RoleModel(Base):
    __tablename__ = 'role'
    id = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid4)
    name = Column(String())
    project_code = Column(String())
    time_created = Column(DateTime(), default=datetime.utcnow)
    is_default = Column(Boolean(), default=False)

    def to_dict(self):
        result = {}
        field_list = [
            'id',
            'name',
            'project_code',
            'time_created',
            'is_default',
        ]
        for field in field_list:
            if field == 'is_default':
                result[field] = getattr(self, field)
            else:
                result[field] = str(getattr(self, field))
        return result

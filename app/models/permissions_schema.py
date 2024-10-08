# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from app.models.base_models import APIResponse


class ListPermissions(BaseModel):
    page: int = 0
    page_size: int = 25
    order_by: str = 'category'
    order_type: str = 'asc'
    project_code: str


class ListPermissionsResponse(APIResponse):
    result: dict = Field(
        {},
        example={},
    )


class CreatePermission(BaseModel):
    project_role: str
    project_code: str


class CreatePermissionResponse(APIResponse):
    result: str = Field(
        '',
        example='success',
    )


class DeletePermission(BaseModel):
    project_role: str
    project_code: str


class DeletePermissionResponse(APIResponse):
    result: str = Field(
        '',
        example='success',
    )


class CreatePermissionsBulk(BaseModel):
    """Bulk create casbin permissions request model."""

    project_code: str
    rules: dict[str, list[str]]


class CreatePermissionsBulkResponse(APIResponse):
    """Bulk create casbin permissions response model."""

    result: str = Field(
        '',
        example='success',
    )


class DeletePermissionsBulk(BaseModel):
    """Bulk delete casbin permissions request model."""

    project_code: str
    rules: dict[str, list[str]]


class CreateRole(BaseModel):
    """Create role request model."""

    name: str
    project_code: str
    is_default: bool = False


class CreateRoleResponse(APIResponse):
    """Create role response model."""

    result: str = Field(
        '',
        example='success',
    )


class RuleModel(BaseModel):
    """Casbin Rule Model."""

    ptype: Optional[str]
    v0: Optional[str]
    v1: str
    v2: str
    v3: str
    v4: str


class ListRoles(BaseModel):
    project_code: str
    order_by: str = 'time_created'
    order_type: str = 'asc'


class ListRolesResponse(APIResponse):
    result: list = Field(
        list[dict],
        example=[
            {
                'name': 'examplerole',
                'time_created': '2022-01-01 01:01:01',
                'project_code': 'exampleproject',
                'is_default': False,
            }
        ],
    )

# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from pydantic import BaseModel
from pydantic import Field

from app.models.base_models import APIResponse


class UserADGroupOperationsPUT(BaseModel):
    """User authentication model."""

    operation_type: str
    group_code: str
    user_email: str


class UserManagementV1PUT(BaseModel):
    operation_type: str
    user_email: str
    operator: str = ''


class ADGroupCreatePOST(BaseModel):
    group_name: str
    description: str | None = ''


class ADGroupCreatePOSTResponse(APIResponse):
    result: str = Field(example='success')


class ADGroupCreateDELETE(BaseModel):
    group_name: str


class ADGroupCreateDELETEResponse(APIResponse):
    result: str = Field(example='success')

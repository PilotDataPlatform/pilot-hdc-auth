# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from app.models.api_response import EAPIResponseCode
from app.models.base_models import APIResponse
from app.resources.error_handler import APIException


class InvitationPUT(BaseModel):
    status: str = ''

    @validator('status')
    def validate_status(cls, v):
        if v not in ['complete', 'pending']:
            raise APIException(status_code=EAPIResponseCode.bad_request.value, error_msg='Invalid status')
        return v


class InvitationListPOST(BaseModel):
    page: int = 0
    page_size: int = 25
    order_by: str = 'create_timestamp'
    order_type: str = 'asc'
    filters: dict = {}


class InvitationPOST(BaseModel):
    email: str
    platform_role: str
    relationship: dict = {}
    invited_by: str
    inviter_project_role: str = ''

    @validator('relationship')
    def validate_relationship(cls, v):
        if not v:
            return v
        for key in ['project_role', 'inviter']:
            if key not in v.keys():
                raise APIException(
                    status_code=EAPIResponseCode.bad_request.value,
                    error_msg=f'relationship missing required value {key}',
                )
        return v

    @validator('platform_role')
    def validate_platform_role(cls, v):
        if v not in ['admin', 'member']:
            raise APIException(status_code=EAPIResponseCode.bad_request.value, error_msg='Invalid platform_role')
        return v

    @validator('inviter_project_role')
    def validate_inviter_project_role(cls, v):
        if not v:
            return v
        if v not in ['platform_admin', 'admin', 'contributor', 'collaborator']:
            raise APIException(status_code=EAPIResponseCode.bad_request.value, error_msg='Invalid project_role')
        return v


class InvitationPOSTResponse(APIResponse):
    result: dict = Field(
        {},
        example={},
    )

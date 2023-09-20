# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from app.models.api_response import APIResponse


class UserGroupPOST(BaseModel):
    username: str
    groupname: str


class UserOpsPOST(BaseModel):
    class Announcement(BaseModel):
        project_code: str
        announcement_pk: str

    username: str
    last_login: Optional[bool]
    announcement: Optional[Announcement]


class RealmRolesPOST(BaseModel):
    project_roles: list
    project_code: str


class UserInRolePOST(BaseModel):
    role_names: list
    username: str = None
    email: str = None
    page: int = 0
    page_size: int = 10
    order_by: str = None
    order_type: str = 'asc'
    status: str = 'active'


class GETUserStatsResponse(APIResponse):
    result: dict = Field({}, example={'admin': 20, 'contributor': 5, 'collaborator': 10})

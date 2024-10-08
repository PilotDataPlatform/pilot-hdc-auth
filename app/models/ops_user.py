# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from pydantic import BaseModel


class UserAuthPOST(BaseModel):
    """user authentication model."""

    username: str
    password: str


class UserTokenRefreshPOST(BaseModel):
    """user token refresh model."""

    refreshtoken: str


class UserLastLoginPOST(BaseModel):
    username: str


class UserProjectRolePOST(BaseModel):
    email: str
    project_role: str
    operator: str = ''
    project_code: str = ''
    # vm_password_requested: bool = False
    invite_event: bool = False


class UserProjectRolePUT(BaseModel):
    email: str
    project_role: str
    operator: str
    project_code: str


class UserProjectRoleDELETE(BaseModel):
    email: str
    project_role: str
    operator: str
    project_code: str


class UserAnnouncementPOST(BaseModel):
    project_code: str
    announcement_pk: str
    username: str

# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from pydantic import BaseModel


class UserCreatePOST(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    project_code: str = ''
    project_role: str = ''


class VMUserCreatePOST(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    project_code: str = ''


class VMUserPasswordResetPOST(BaseModel):
    username: str

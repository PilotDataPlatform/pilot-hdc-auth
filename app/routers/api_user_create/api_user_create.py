# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi_utils import cbv

from app.models.api_response import APIResponse
from app.models.user_create import UserCreatePOST
from app.services.data_providers.identity_client import get_identity_client

router = APIRouter()

_API_TAG = '/v1/admin'
_API_NAMESPACE = 'api_auth'


@cbv.cbv(router)
class UserCreate:
    @router.post('/admin/users', tags=[_API_TAG], summary='Create a new user in LDAP')
    async def post(self, data: UserCreatePOST):
        IdentityClient = get_identity_client()
        async with IdentityClient() as client:
            result = await client.create_user(
                username=data.username,
                email=data.email,
                first_name=data.first_name,
                last_name=data.last_name,
                password=data.password,
            )
            api_response = APIResponse()
            api_response.result = result
            return api_response.json_response()

# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import secrets
import string

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from fastapi_utils import cbv

from app.logger import AuditLog
from app.logger import logger
from app.models.user_create import VMUserCreatePOST
from app.models.user_create import VMUserPasswordResetPOST
from app.services.data_providers.freeipa_client import FreeIPAClient
from app.services.data_providers.freeipa_client import get_freeipa_client

router = APIRouter()

_API_TAG = 'VM'
_API_NAMESPACE = 'vm_user_management'


@cbv.cbv(router)
class HBACOperations:
    @router.get('/vm/hbac', tags=[_API_TAG], summary='find rule by name')
    async def find_hbac(
        self,
        name: str,
        freeipa_client: FreeIPAClient = Depends(get_freeipa_client),
    ) -> Response:
        """
        Summary:
            The api is used to find an HBAC rule by name.

        Parameters:
            - name(string): HBAC rule name

        Return:
            Full rule description
        """

        logger.info(f'Call API to find an HBAC rule with name {name}')

        async with freeipa_client:
            rule = await freeipa_client.get_hbac_rule_by_name(name)

        return JSONResponse(status_code=200, content=rule)

    @router.post('/vm/hbac/add', tags=[_API_TAG], summary='add the target user to hbac rule')
    async def add_user_to_hbac(
        self,
        username: str,
        rule: str,
        freeipa_client: FreeIPAClient = Depends(get_freeipa_client),
    ) -> Response:
        """
        Summary:
            The api is used to directly add the user to HBAC rule.

        Payload:
            - email(string): user email
            - rule(string): HBAC rule name

        Return:
            200 added
        """

        logger.info('Call API to add a user to HBAC rule')

        async with freeipa_client:
            hbac_rule = await freeipa_client.get_hbac_rule_by_name(rule)
            await freeipa_client.add_user_to_hbac_rule(username, hbac_rule['name'])
            message = f"User {username} was added to rule {hbac_rule['name']}"
            logger.info(message)

        return Response(status_code=200, content=message)

    @router.delete('/vm/hbac/remove', tags=[_API_TAG], summary='remove the target user from hbac rule')
    async def remove_user_from_hbac(
        self,
        username: str,
        rule: str,
        freeipa_client: FreeIPAClient = Depends(get_freeipa_client),
    ) -> Response:
        """
        Summary:
            The api is used to remove the user from HBAC rule.

        Payload:
            - username(string): username
            - rule(string): HBAC rule name

        Return:
            200 removed
        """

        logger.info('Call API to remove a user from HBAC rule')

        async with freeipa_client:
            hbac_rule = await freeipa_client.get_hbac_rule_by_name(rule)
            if username in hbac_rule['members']:
                await freeipa_client.remove_user_from_hbac_rule(username, hbac_rule['name'])
                message = f"User {username} was removed from rule {hbac_rule['name']}"
                logger.info(message)
            else:
                message = f"User {username} was not part of rule {hbac_rule['name']}"
                logger.info(message)

        return Response(status_code=200, content=message)


@cbv.cbv(router)
class VMUserOperations:
    @router.get('/vm/user', tags=[_API_TAG], summary='Find VM user by username')
    async def find_user(
        self,
        username: str,
        freeipa_client: FreeIPAClient = Depends(get_freeipa_client),
    ) -> Response:

        logger.info('Call API to find a user by email')

        with AuditLog('find VM user', username=username):
            async with freeipa_client:
                user = await freeipa_client.get_user_by_username(username)

        return JSONResponse(content=user)

    @router.post('/vm/user', tags=[_API_TAG], summary='Directly create new user for VM')
    async def create_user(
        self,
        data: VMUserCreatePOST,
        freeipa_client: FreeIPAClient = Depends(get_freeipa_client),
    ) -> Response:

        logger.info('Call API to create new user for VM')

        with AuditLog('create user for VM', username=data.username):
            async with freeipa_client:
                user = await freeipa_client.create_user(
                    username=data.username,
                    email=data.email,
                    first_name=data.first_name,
                    last_name=data.last_name,
                    password=data.password,
                )

        logger.info(f'Successfully created user {data.username}')
        return JSONResponse(content=user)

    @router.post('/vm/user/reset', tags=[_API_TAG], summary='Reset user password for VM')
    async def reset_password(
        self,
        data: VMUserPasswordResetPOST,
        freeipa_client: FreeIPAClient = Depends(get_freeipa_client),
    ) -> Response:

        logger.info('Call API to reset user password for VM')

        with AuditLog('reset password for VM user', username=data.username):
            async with freeipa_client:
                # password of length 10, only numbers
                new_password = ''.join(secrets.choice(string.ascii_lowercase) for i in range(10))
                await freeipa_client.reset_password(
                    username=data.username,
                    new_password=new_password,
                )

        result = {'username': data.username, 'password': new_password}
        logger.info(f'Successfully reset password for user {data.username}')
        return JSONResponse(content=result)

    @router.put('/vm/user', tags=[_API_TAG], summary='Create or modify user to have access to projects VM')
    async def create_or_modify_user(
        self,
        data: VMUserCreatePOST,
        freeipa_client: FreeIPAClient = Depends(get_freeipa_client),
    ) -> Response:

        logger.info('Call API to create new user for VM')

        with AuditLog('create or modify user for VM', username=data.username):
            async with freeipa_client:
                try:
                    user = await freeipa_client.get_user_by_username(data.username)
                except HTTPException:
                    user = await freeipa_client.create_user(
                        username=data.username,
                        email=data.email,
                        first_name=data.first_name,
                        last_name=data.last_name,
                        password=data.password,
                    )
                    logger.info(f'Creating user {data.username} for first-time accessing the VMs')

                rule = await freeipa_client.get_hbac_rule_by_name(data.project_code)

                await freeipa_client.add_user_to_hbac_rule(user['username'], rule['name'])

        message = f'User {user["username"]} was granted access to VM for project {data.project_code}'
        logger.info(message)
        return Response(status_code=200, content=message)

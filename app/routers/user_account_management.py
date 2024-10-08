# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends
from fastapi_utils import cbv

from app.commons.psql_services.user_event import create_event
from app.components.identity.crud import IdentityCRUD
from app.components.identity.dependencies import get_identity_crud
from app.config import ConfigSettings
from app.logger import logger
from app.models.api_response import APIResponse
from app.models.api_response import EAPIResponseCode
from app.models.user_account_management import ADGroupCreateDELETE
from app.models.user_account_management import ADGroupCreateDELETEResponse
from app.models.user_account_management import ADGroupCreatePOST
from app.models.user_account_management import ADGroupCreatePOSTResponse
from app.models.user_account_management import UserADGroupOperationsPUT
from app.models.user_account_management import UserManagementV1PUT
from app.resources.error_handler import APIException
from app.resources.error_handler import catch_internal
from app.services.data_providers.identity_client import get_identity_client

router = APIRouter()

_API_TAG = 'v1/user/account'
_API_NAMESPACE = 'api_user_management'


@cbv.cbv(router)
class UserADGroupOperations:
    @router.put('/user/group', tags=[_API_TAG], summary='add the target user to ad group')
    @catch_internal(_API_NAMESPACE)
    async def put(self, data: UserADGroupOperationsPUT):
        """
        Summary:
            The api is used to directly add the user to ldap group.
            inside ldap the group name will be <prefix>-<group_code>

        Payload(UserManagementV1PUT):
            - operation_type(string): only accept remove or add
            - user_email(string): the target user email
            - group_code(string): the group code define by upperstream

        Return:
            200 updated
        """

        logger.info('Call API for user ad group operations')

        response = APIResponse()
        operation_type = data.operation_type
        group_code = data.group_code
        user_email = data.user_email

        try:
            IdentityClient = get_identity_client()
            async with IdentityClient() as client:
                if operation_type == 'remove':
                    await client.remove_user_from_group(user_email, client.format_group_name(group_code))
                elif operation_type == 'add':
                    await client.add_user_to_group(user_email, client.format_group_name(group_code))

                response.result = f'{operation_type} user {user_email} from ad group'
                response.code = EAPIResponseCode.success

        except Exception as e:
            msg = 'Failed to add user to group'
            logger.error(f'{msg}: {e.content.get("error_msg")}')
            response.error_msg = msg
            response.code = EAPIResponseCode.internal_error
            response.total = 0

        return response.json_response()

    @router.post(
        '/user/group', tags=[_API_TAG], response_model=ADGroupCreatePOSTResponse, summary='create a ad/ldap group'
    )
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: ADGroupCreatePOST):
        """
        Summary:
            create a ad/ldap group

        Payload:
            - group_name(string): Group name without a prefix
            - description (string): Group description

        Return:
            200
        """
        logger.info('Call API for user ad group creation')

        response = APIResponse()

        try:
            IdentityClient = get_identity_client()
            async with IdentityClient() as client:
                group_name = client.format_group_name(data.group_name)
                await client.create_group(group_name, data.description)
        except Exception as e:
            msg = 'Failed to create group'
            logger.error(f'{msg}: {e.content.get("error_msg")}')
            response.error_msg = msg
            response.code = EAPIResponseCode.internal_error
            response.total = 0

        return response.json_response()

    @router.delete(
        '/user/group', tags=[_API_TAG], response_model=ADGroupCreateDELETEResponse, summary='delete a ad/ldap group'
    )
    @catch_internal(_API_NAMESPACE)
    async def delete(self, data: ADGroupCreateDELETE):
        """
        Summary:
            delete a ad/ldap group

        Payload:
            - group_name(string): Group name without a prefix

        Return:
            200
        """
        logger.info('Call API for user ad group creation')

        response = APIResponse()

        try:
            IdentityClient = get_identity_client()
            async with IdentityClient() as client:
                await client.delete_group(client.format_group_name(data.group_name))
        except Exception as e:
            msg = 'Failed to delete group'
            logger.error(f'{msg}: {e.content.get("error_msg")}')
            if type(e) == APIException:
                response.error_msg = e.content.get('error_msg')
                response.code = e.status_code
            else:
                response.error_msg = msg
                response.code = EAPIResponseCode.internal_error
                response.total = 0

        return response.json_response()


@cbv.cbv(router)
class UserManagementV1:
    @router.put('/user/account', tags=[_API_TAG], summary='add the new user to ad')
    @catch_internal(_API_NAMESPACE)
    async def put(self, data: UserManagementV1PUT, identity_crud: IdentityCRUD = Depends(get_identity_crud)):
        """
        Summary:
            The api is used to disable/enable users in portal. It is using
            keycloak api to setup the `status` of user attribute in keyloack
            to reflect disable or enable. user will be removed from ALL assigned
            realm role(all permissions)
            The ldap client is alse used to remove the user from corresponding DN
            in ldap

        Payload(UserManagementV1PUT):
            - operation_type(string): only accept disable or enable
            - user_email(string): the target user email

        Return:
            204 updated

        """

        logger.info('Call API for update user accounts')

        res = APIResponse()
        try:
            operation_type = data.operation_type
            user_email = data.user_email

            if operation_type not in ['enable', 'disable']:
                res.error_msg = f'operation {operation_type} is not allowed'
                res.code = EAPIResponseCode.bad_request
                return res.json_response()

            status = {
                'enable': 'active',
                'disable': 'disabled',
            }.get(operation_type)

            kc_cli = await identity_crud.create_operations_admin()
            user = await kc_cli.get_user_by_email(user_email)
            user_id = user.get('id')
            await kc_cli.update_user_attributes(user_id, {'status': status})

            if operation_type == 'disable':
                realm_role = await identity_crud.get_user_realm_roles(user_id)
                deleted_roles = [x for x in realm_role if x.get('name') != 'uma_authorization']
                await kc_cli.remove_user_realm_roles(user_id, deleted_roles)
                await kc_cli.keycloak_admin.update_user(user_id, payload={'enabled': False})

                IdentityClient = get_identity_client()
                async with IdentityClient() as client:
                    identity_user = await client.get_user_by_email(user_email)
                    groups = identity_user['groups']
                    for group_name in groups:
                        if ConfigSettings.LDAP_USER_GROUP not in group_name:
                            if group_name.startswith(ConfigSettings.LDAP_PREFIX):
                                await client.remove_user_from_group(identity_user['email'], group_name)
            else:
                await kc_cli.keycloak_admin.update_user(user_id, payload={'enabled': True})

            if operation_type == 'disable':
                event_type = 'ACCOUNT_DISABLE'
            else:
                event_type = 'ACCOUNT_ACTIVATED'
            await create_event(
                {
                    'target_user_id': user['id'],
                    'target_user': user['username'],
                    'operator': data.operator,
                    'operator_id': '',
                    'event_type': event_type,
                    'detail': {},
                },
                identity_crud=identity_crud,
            )

            res.result = f'{operation_type} user {user_email}'
            res.code = EAPIResponseCode.success

        except Exception as e:
            logger.error(f'[Internal error] {e.content.get("error_msg")}')
            res.error_msg = f'[Internal error] {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()

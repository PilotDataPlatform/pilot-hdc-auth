# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import math
from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from fastapi_utils import cbv
from keycloak import exceptions

from app.commons.notification import record_newsfeed_notification
from app.commons.psql_services.user_event import create_event
from app.components.identity.crud import IdentityCRUD
from app.components.identity.dependencies import get_identity_crud
from app.config import ConfigSettings
from app.models.api_response import APIResponse
from app.models.api_response import EAPIResponseCode
from app.models.ops_user import UserAuthPOST
from app.models.ops_user import UserProjectRolePOST
from app.models.ops_user import UserProjectRolePUT
from app.models.ops_user import UserTokenRefreshPOST
from app.resources.error_handler import APIException
from app.resources.error_handler import catch_internal
from app.resources.keycloak_api.ops_user import OperationsUser

router = APIRouter()
_API_TAG = 'v1/auth'
_API_NAMESPACE = 'api_auth'


@cbv.cbv(router)
class UserAuth:
    @router.post(
        '/users/auth',
        tags=[_API_TAG],
        summary='make the user authentication and return the access token',
    )
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserAuthPOST, identity_crud: IdentityCRUD = Depends(get_identity_crud)):
        """
        Summary:
            The api is using keycloak api to authenticate user and return
            the access_token and refresh_token. The user with disabled status
            cannot be login

        Payload:
            - username(string): The login string for user
            - password(string): login credential stored in keycloak

        Return:
            - access token
            - refresh token
        """

        res = APIResponse()
        try:
            username = data.username
            password = data.password

            realm = ConfigSettings.KEYCLOAK_REALM
            client_id = ConfigSettings.KEYCLOAK_CLIENT_ID
            client_secret = ConfigSettings.KEYCLOAK_SECRET

            user_client = await OperationsUser.create(client_id, realm, client_secret)
            admin_client = await identity_crud.create_operations_admin()
            token = await user_client.get_token(username, password)
            user_info = await identity_crud.get_user_by_username(username)
            if user_info.get('attributes', {}).get('status', ['disabled']) == ['disabled']:
                raise exceptions.KeycloakAuthenticationError('User is disabled')

            user_id = user_info.get('id')
            last_login = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
            await admin_client.update_user_attributes(user_id, {'last_login': last_login})

            res.result = token
            res.code = EAPIResponseCode.success
        except exceptions.KeycloakAuthenticationError as err:
            res.error_msg = str(err)
            res.code = EAPIResponseCode.unauthorized
        except exceptions.KeycloakGetError as err:
            res.error_msg = str(err)
            res.code = EAPIResponseCode.not_found
        except Exception as e:
            res.error_msg = f'User authentication failed : {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


@cbv.cbv(router)
class UserRefresh:
    @router.post(
        '/users/refresh',
        tags=[_API_TAG],
        summary='refresh the user token and issue a new one',
    )
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserTokenRefreshPOST, identity_crud: IdentityCRUD = Depends(get_identity_crud)):
        """
        Summary:
            The api is using keycloak api to return a new refresh
            token for futher usage

        Payload:
            - refreshtoken(string): The expiring refresh token from
                same issuer/client in keycloak

        Return:
            - refresh token
        """

        res = APIResponse()
        try:
            token = data.refreshtoken

            realm = ConfigSettings.KEYCLOAK_REALM
            client_id = ConfigSettings.KEYCLOAK_CLIENT_ID
            client_secret = ConfigSettings.KEYCLOAK_SECRET
            user_client = await OperationsUser.create(client_id, realm, client_secret)
            token = await user_client.get_refresh_token(token)

            res.result = token
            res.code = EAPIResponseCode.success
        except Exception as e:
            res.error_msg = f'Unable to get token : {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


@cbv.cbv(router)
class UserProjectRole:
    identity_crud: IdentityCRUD = Depends(get_identity_crud)

    @router.put('/user/project-role', tags=[_API_TAG], summary='change a users project role')
    async def change_role(self, data: UserProjectRolePUT):
        """
        Summary:
            The api is using keycloak api to add a user into existing keyclaok realm role and remove then from there
            previous role group

        Payload:
            - email(string): The unique email for the user to identiy
            - project_role(string): The target realm role for new role

        Return:
            - 200 success
        """

        res = APIResponse()
        email = data.email
        realm_role = data.project_role

        try:
            admin_client = await self.identity_crud.create_operations_admin()
            user = await admin_client.get_user_by_email(email)
            roles = await self.identity_crud.get_user_realm_roles(user['id'])

            old_role = ''
            for role in roles:
                if realm_role.split('-')[0] in role['name']:
                    old_role = role['name']
                    await admin_client.delete_role_of_user(user['id'], role['name'])
                    break
            await admin_client.assign_user_role(user['id'], realm_role)

            res.result = 'success'
            res.code = EAPIResponseCode.success

        except Exception as e:
            error_msg = f'Fail to add user to group: {e}'
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

        old_role = old_role.split('-')[1]
        new_role = realm_role.split('-')[1]
        await create_event(
            {
                'target_user_id': user['id'],
                'target_user': user['username'],
                'operator': data.operator,
                'event_type': 'ROLE_CHANGE',
                'detail': {
                    'to': new_role,
                    'from': old_role,
                    'project_code': data.project_code,
                },
            },
            identity_crud=self.identity_crud,
        )
        await record_newsfeed_notification(
            {
                'recipient_username': user['username'],
                'initiator_username': data.operator,
                'project_code': data.project_code,
                'current_role': new_role,
                'previous_role': old_role,
            }
        )
        return res.json_response()

    @router.post(
        '/user/project-role',
        tags=[_API_TAG],
        summary='list the project role for given user',
    )
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserProjectRolePOST):
        """
        Summary:
            The api is using keycloak api to add a user into existing
            keyclaok realm role

        Payload:
            - email(string): The unique email for the user to identiy
            - project_role(string): The target realm role

        Return:
            - 200 success
        """

        res = APIResponse()
        email = data.email
        realm_role = data.project_role

        try:
            admin_client = await self.identity_crud.create_operations_admin()
            user = await admin_client.get_user_by_email(email)
            await admin_client.assign_user_role(user['id'], realm_role)

            res.result = 'success'
            res.code = EAPIResponseCode.success

        except Exception as e:
            res.error_msg = f'Fail to add user to group: {e}'
            res.code = EAPIResponseCode.internal_error

        if data.invite_event:
            await create_event(
                {
                    'target_user_id': user['id'],
                    'target_user': user['username'],
                    'operator': data.operator,
                    'event_type': 'INVITE_TO_PROJECT',
                    'detail': {
                        'project_code': data.project_code,
                        'project_role': realm_role.replace(data.project_code + '-', ''),
                        'platform_role': 'member',
                    },
                },
                identity_crud=self.identity_crud,
            )

        return res.json_response()

    @router.delete(
        '/user/project-role',
        tags=[_API_TAG],
        summary='remove the project role for given user',
    )
    @catch_internal(_API_NAMESPACE)
    async def delete(self, email: str, project_role: str, operator: str, project_code: str):
        """
        Summary:
            The api is using keycloak api to add a user into existing
            keyclaok realm role

        Parameter:
            - email(string): The unique email for the user to identiy
            - project_role(string): The target realm role
            - operator(string): The operator that remove the user
            - project_code(string): The project code that user takes place

        Return:
            - 200 success
        """

        res = APIResponse()

        try:
            admin_client = await self.identity_crud.create_operations_admin()
            user = await admin_client.get_user_by_email(email)
            await admin_client.delete_role_of_user(user['id'], project_role)

            res.result = 'success'
            res.code = EAPIResponseCode.success
        except Exception as e:
            res.error_msg = f'Fail to remove user from group: {e}'
            res.code = EAPIResponseCode.internal_error

        await create_event(
            {
                'target_user_id': user['id'],
                'target_user': user['username'],
                'operator': operator,
                'event_type': 'REMOVE_FROM_PROJECT',
                'detail': {
                    'project_code': project_code,
                },
            },
            identity_crud=self.identity_crud,
        )
        return res.json_response()


@cbv.cbv(router)
class UserList:
    @router.get('/users', tags=[_API_TAG], summary='list users from keycloak')
    @catch_internal(_API_NAMESPACE)
    async def get(  # noqa: C901
        self,
        username: str = None,
        email: str = None,
        page: int = 0,
        page_size: int = 10,
        status: str = None,
        role: str = None,
        order_by: str = None,
        order_type: str = 'asc',
        identity_crud: IdentityCRUD = Depends(get_identity_crud),
    ):
        """
        Summary:
            The api is used to the keycloak api and python to list all
            user under the platform.
            for now the api does not support the exact search and status check
            This will need to be wait until keycloak is upto v16
            The native api does not support join/sorting, so I temporary do them manually
            ALL the in memory sorting, searching, mapping are the temporary solution
            at the end, they will be sync to some primary db

        Parameter:
            - order_by(string optional): the field will be ordered by.
            - order_type(string optional): default=asc. support asc or desc.
            - page(int): default=0, the pagination to indicate current page.
            - page_size(int): default=10, the return user size.
            - username(string optional): if payload has username, the api will
                return all user contains target username.
            - email(string optional): if payload has email, the api will
                return all user contains target email.
            - status(string): not support yet

        Return:
            - user list
                - username
                - id
                - email
                - status
        """

        res = APIResponse()

        try:
            admin_client = await identity_crud.create_operations_admin()
            total_users = await admin_client.get_user_count()

            users = None
            if role == 'admin':
                users = await admin_client.get_users_in_role('platform-admin')
            else:
                users = await admin_client.get_all_users(max_users=total_users)
            user_list = [user for user in users if user.get('attributes', {}).get('status')]
            if username:
                user_list = [user for user in user_list if username in user.get('username')]
            if email:
                user_list = [user for user in user_list if email in user.get('email')]
            if status:
                user_list = [user for user in user_list if status in user.get('attributes', {}).get('status')]

            if order_by:
                order_by = {
                    'first_name': 'firstName',
                    'last_name': 'lastName',
                    'name': 'username',
                }.get(order_by, order_by)

                if not (
                    order_by
                    in [
                        'id',
                        'username',
                        'lastName',
                        'firstName',
                        'email',
                        'username',
                        'time_created',
                        'last_login',
                    ]
                ):
                    res.error_msg = f'the order_by {order_by} field does not exist'
                    res.code = EAPIResponseCode.bad_request
                    return res.json_response()

                order_lambda = lambda user: user.get(order_by, '')  # noqa: E731
                if order_by == 'last_login':
                    order_lambda = lambda user: user.get('attributes').get('last_login', [''])[0]  # noqa: E731
                elif order_by == 'time_created':
                    order_lambda = lambda user: user.get('createdTimestamp', '')  # noqa: E731

                user_list = sorted(
                    user_list,
                    key=order_lambda,
                    reverse=True if order_type == 'desc' else False,
                )

            user_count = len(user_list)
            user_list = [
                {
                    'id': user.get('id'),
                    'name': user.get('username'),
                    'username': user.get('username'),
                    'first_name': user.get('firstName'),
                    'last_name': user.get('lastName'),
                    'email': user.get('email'),
                    'time_created': datetime.fromtimestamp(user.get('createdTimestamp', 0) // 1000).strftime(
                        '%Y-%m-%dT%H:%M:%S'
                    ),
                    'last_login': user.get('attributes', {}).get('last_login', [None])[0],
                    'status': user.get('attributes', {}).get('status', ['disabled'])[0],
                }
                for user in user_list[page * page_size : (page + 1) * page_size]
            ]

            admins = await admin_client.get_users_in_role('platform-admin')
            platform_admins = [x.get('username') for x in admins]
            for user in user_list:
                if user.get('name') in platform_admins:
                    user.update({'role': 'admin'})
                else:
                    user.update({'role': 'member'})

            res.result = user_list
            res.total = user_count
            res.num_of_pages = math.ceil(user_count / page_size)
            res.page = page

        except Exception as e:
            res.error_msg = str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()

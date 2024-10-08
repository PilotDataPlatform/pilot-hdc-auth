# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import math
from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from fastapi.concurrency import run_in_threadpool
from fastapi_utils import cbv
from keycloak import exceptions

from app.commons.psql_services.permissions import create_role_record
from app.components.identity.crud import IdentityCRUD
from app.components.identity.dependencies import get_identity_crud
from app.logger import logger
from app.models.api_response import APIResponse
from app.models.api_response import EAPIResponseCode
from app.models.ops_admin import GETUserStatsResponse
from app.models.ops_admin import RealmRolesPOST
from app.models.ops_admin import UserGroupPOST
from app.models.ops_admin import UserInRolePOST
from app.models.ops_admin import UserOpsPOST
from app.resources.error_handler import catch_internal

router = APIRouter()

_API_TAG = '/v1/admin'
_API_NAMESPACE = 'api_admin_ops'


@cbv.cbv(router)
class UserOps:
    identity_crud: IdentityCRUD = Depends(get_identity_crud)

    @router.get('/admin/user', tags=[_API_TAG], summary='get user infomation by one of email, username, user_id')
    @catch_internal(_API_NAMESPACE)
    async def get(self, email: str = None, username: str = None, user_id: str = None):  # noqa: C901
        """
        Summary:
            The api is used to the keycloak api to get user info
            including attributes

        Parameter:
            - email(string): the email from target user
            - username(string): the useranme from target user
            - user_id(string): the hash id from keycloak

        Return:
            - user information(dict)
        """

        res = APIResponse()

        try:
            if not any([username, email, user_id]):
                res.error_msg = 'One of email, username, user_id is mandetory'
                res.code = EAPIResponseCode.bad_request
                return res.json_response()

            admin_client = await self.identity_crud.create_operations_admin()

            logger.info(f'Getting user info for: {email} - {username} - {user_id}')
            user_info = None
            if email:
                user_info = await admin_client.get_user_by_email(email)
            elif username:
                user_info = await self.identity_crud.get_user_by_username(username)
            elif user_id:
                user_info = await admin_client.get_user_by_id(user_id)

            if user_info.get('firstName'):
                user_info.update({'first_name': user_info.pop('firstName')})
            else:
                user_info['first_name'] = ''
            if user_info.get('lastName'):
                user_info.update({'last_name': user_info.pop('lastName')})
            else:
                user_info['last_name'] = ''
            user_info.update({'name': user_info.get('username')})

            user_attribute = user_info.get('attributes', {})
            for x in user_attribute:
                user_attribute.update({x: user_attribute[x][0]})
            if not user_attribute.get('status', None):
                user_attribute.update({'status': 'pending'})
            user_info.update({'attributes': user_attribute})

            realm_roles = await self.identity_crud.get_user_realm_roles(user_info.get('id'))
            platform_admin = [r for r in realm_roles if r.get('name') == 'platform-admin']
            if platform_admin:
                user_info.update({'role': 'admin'})
            else:
                user_info.update({'role': 'member'})

            res.result = user_info
            res.code = EAPIResponseCode.success
        except exceptions.KeycloakGetError:
            res.error_msg = 'user not found'
            res.code = EAPIResponseCode.not_found
        except Exception as e:
            res.error_msg = 'Fail to get user: ' + str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()

    @router.put(
        '/admin/user',
        tags=[_API_TAG],
        summary='currently only support update user attribute of \
                     last login_time and announcement',
    )
    @catch_internal(_API_NAMESPACE)
    async def put(self, data: UserOpsPOST):
        """
        Summary:
            The api is used to the keycloak api to update user
            attributes

        Parameter:
            - last_login(bool optional): indicate if api need to update `last_login`
                attribute. The format will be "%Y-%m-%dT%H:%M:%S"
            - announcement(dict optional): the useranme from target user
                - project_code(string): the unique identifier of project
                - announcement_pk(string): the unique id for announcement
            - username(string): unique username in the keycloak

        Return:
            - user information(dict)
        """

        res = APIResponse()

        last_login = data.last_login
        announcement = data.announcement
        username = data.username

        if not last_login and not announcement:
            res.error_msg = 'last_login or announcement is required'
            res.code = EAPIResponseCode.bad_request
            return res.json_response()

        try:
            admin_client = await self.identity_crud.create_operations_admin()
            user_id = await admin_client.get_user_id(username)

            attri = {}
            if last_login:
                last_login_str = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
                attri.update({'last_login': last_login_str})
            if announcement:
                attri.update({'announcement_' + announcement.project_code: announcement.announcement_pk})
            new_attribute = await admin_client.update_user_attributes(user_id, attri)

            res.result = new_attribute
            res.code = EAPIResponseCode.success
        except exceptions.KeycloakGetError:
            res.error_msg = 'user not found'
            res.code = EAPIResponseCode.not_found
        except Exception as e:
            res.error_msg = str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


@cbv.cbv(router)
class UserGroup:
    identity_crud: IdentityCRUD = Depends(get_identity_crud)

    @router.post('/admin/users/group', tags=[_API_TAG], summary='add user to existing group')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserGroupPOST):
        """
        Summary:
            the api will add the user to the target keycloak group.
            create a new group if the target group is not exist

        Payload:
            - username(string): the useranme from keycloak
            - groupname(string): the unique groupname from keycloak

        Return:
            200 succuss
        """

        res = APIResponse()
        try:
            username = data.username
            groupname = data.groupname

            operations_admin = await self.identity_crud.create_operations_admin()
            user_id = await operations_admin.get_user_id(username)
            group = await operations_admin.get_group_by_name(groupname)
            if not group:
                await operations_admin.create_group(groupname)
                group = await operations_admin.get_group_by_name(groupname)

            await operations_admin.add_user_to_group(user_id, group['id'])
            res.result = 'success'
            res.code = EAPIResponseCode.success
        except Exception as e:
            res.error_msg = 'UserGroup failed' + str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()

    @router.delete('/admin/users/group', tags=[_API_TAG], summary='add user to existing group')
    @catch_internal(_API_NAMESPACE)
    async def delete(self, username: str, groupname: str):
        """
        Summary:
            the function will remove the target user from the
            given keycloak group

        Parameter:
            - username(string): the useranme from keycloak
            - groupname(string): the unique groupname from keycloak

        Return:
            200 succuss
        """

        res = APIResponse()
        try:
            operations_admin = await self.identity_crud.create_operations_admin()
            user_id = await operations_admin.get_user_id(username)
            group = await operations_admin.get_group_by_name(groupname)
            await operations_admin.remove_user_from_group(user_id, group['id'])

            res.result = 'success'
            res.code = EAPIResponseCode.success
        except Exception as e:
            res.error_msg = 'UserGroup delete failed' + str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


@cbv.cbv(router)
class RealmRoles:
    identity_crud: IdentityCRUD = Depends(get_identity_crud)

    @router.get('/admin/users/realm-roles', tags=[_API_TAG], summary="get user's realm roles")
    @catch_internal(_API_NAMESPACE)
    async def get(self, username: str):
        """
        Summary:
            The api is used to the keycloak api to fetch
            specific user's realm roles

        Parameter:
            - username(string): the useranme from target user

        Return:
            - realms infomation(list)
        """

        res = APIResponse()
        try:
            user = await self.identity_crud.get_user_by_username(username)
            user_id = user.get('id')

            result = await self.identity_crud.get_user_realm_roles(user_id)
            res.result = result
            res.code = EAPIResponseCode.success
        except Exception as e:
            res.error_msg = f'get realm roles in keycloak failed: {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()

    @router.post('/admin/users/realm-roles', tags=[_API_TAG], summary='add new realm roles in keycloak')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: RealmRolesPOST):
        """
        Summary:
            The api is used to the keycloak api to create
            realm roles. The new name will be `<project_code>-
            <project_roles>`.

        Parameter:
            - project_roles(list): the list of roles to create in keycloak.
            - project_code(string): the unique code of project.

        Return:
            - 200 success
        """

        res = APIResponse()
        try:
            project_roles = data.project_roles
            project_code = data.project_code
            operations_admin = await self.identity_crud.create_operations_admin()
            await operations_admin.create_project_realm_roles(project_roles, project_code)
            for role in project_roles:
                is_default = role in ['admin', 'contributor', 'collaborator']
                await run_in_threadpool(create_role_record, role, project_code, is_default)

            res.result = 'success'
            res.code = EAPIResponseCode.success
        except Exception as e:
            res.error_msg = f'create realm roles in keycloak failed: {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


@cbv.cbv(router)
class UserInRole:
    @router.post('/admin/roles/users', tags=[_API_TAG], summary='')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserInRolePOST, identity_crud: IdentityCRUD = Depends(get_identity_crud)):
        """
        Summary:
            The api is used to the keycloak api and python to query
            user list under target realm roles.
            The native api does not support any seaching/join/sorting/pagination,
            so I temporary do them manually.
            ALL the in memory sorting, searching, mapping are the temporary solution
            at the end, they will be sync to some primary db.

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
            - 200 list of users
                - username
                - email
                - attributes
        """

        res = APIResponse()
        order_by = data.order_by
        order_type = data.order_type
        page = data.page
        page_size = data.page_size
        username = data.username
        email = data.email

        total_users = 0
        try:
            admin_client = await identity_crud.create_operations_admin()
            user_list = []
            for role in data.role_names:
                user_in_role = await admin_client.get_users_in_role(role)

                user_list += [
                    {
                        'id': user.get('id'),
                        'name': user.get('username'),
                        'username': user.get('username'),
                        'first_name': user.get('firstName'),
                        'last_name': user.get('lastName'),
                        'email': user.get('email'),
                        'permission': role.split('-')[-1],
                        'time_created': datetime.fromtimestamp(user.get('createdTimestamp', 0) // 1000).strftime(
                            '%Y-%m-%dT%H:%M:%S'
                        ),
                    }
                    for user in user_in_role
                ]

            if username:
                user_list = [user for user in user_list if user.get('name') and username in user.get('name')]
            if email:
                user_list = [user for user in user_list if user.get('email') and email in user.get('email')]
            if order_by:
                if not (
                    order_by
                    in ['id', 'name', 'first_name', 'last_name', 'email', 'permission', 'username', 'time_created']
                ):
                    res.error_msg = f'the order_by {order_by} field does not exist'
                    res.code = EAPIResponseCode.bad_request
                    return res.json_response()

                order_lambda = lambda user: user.get(order_by, '')  # noqa: E731
                if order_by == 'time_created':
                    order_lambda = lambda user: user.get('attributes', {}).get('createTimestamp', [''])[0]  # noqa: E731
                user_list = sorted(user_list, key=order_lambda, reverse=True if order_type == 'desc' else False)

            total_users = len(user_list)
            user_list = user_list[page * page_size : (page + 1) * page_size]
            res.result = user_list
            res.total = total_users
            res.num_of_pages = math.ceil(total_users / page_size)
            res.page = page
        except Exception as e:
            res.error_msg = str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


@cbv.cbv(router)
class UserInRoleStats:
    @router.get(
        '/admin/roles/users/stats',
        tags=[_API_TAG],
        response_model=GETUserStatsResponse,
        summary='Get user number per realm role for a project',
    )
    @catch_internal(_API_NAMESPACE)
    async def get(self, project_code: str, identity_crud: IdentityCRUD = Depends(get_identity_crud)):
        """
        Summary:
            Uses keycloak api to retrieve number of users under all realm roles for a given project.

        Return:
            - 200 dictionary of number of users per realm role
        """

        res = APIResponse()

        try:
            admin_client = await identity_crud.create_operations_admin()
            role_count = {}
            for role in ['admin', 'contributor', 'collaborator']:
                users_found = await admin_client.get_users_in_role(f'{project_code}-{role}')
                role_count[role] = len(users_found)
            res.result = role_count
        except Exception as e:
            res.error_msg = str(e)
            res.code = EAPIResponseCode.internal_error
        return res.json_response()

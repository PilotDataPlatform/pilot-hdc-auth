# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any

import httpx
from keycloak import KeycloakAdmin
from keycloak import exceptions
from requests import Response

from app.config import ConfigSettings


class OperationsAdmin:

    keycloak_admin: KeycloakAdmin

    def __init__(self, keycloak_admin: KeycloakAdmin, realm_name: str, headers: dict[str, Any]) -> None:
        self.keycloak_admin = keycloak_admin
        self.realm_name = realm_name
        self.header = headers

    async def get_user_id(self, username: str) -> str:
        """
        Summary:
            The wraped for python keycloak client to get user id by username

        Parameter:
            - username(string): target username

        Return:
            - user_id(string): the hash id from keycloak
        """

        user_id = await self.keycloak_admin.get_user_id(username)
        return user_id

    async def get_user_by_id(self, user_id: str) -> dict:
        """
        Summary:
            The wraped for python keycloak client to get user infomation
            by id

        Parameter:
            - userid(string): the hash id from keycloak

        Return:
            - user(dict): the user infomation from keycloak
        """

        user = await self.keycloak_admin.get_user(user_id)
        return user

    async def get_user_by_email(self, email: str) -> dict:
        """
        Summary:
            The wraped for python keycloak client to get user infomation
            by email

        Parameter:
            - email(string): the email for target user

        Return:
            - user(dict): the user infomation from keycloak
        """

        users = await self.keycloak_admin.get_users({'email': email})
        return next((user for user in users if user['email'] == email), None)

    async def get_user_by_username(self, username: str) -> dict:
        """
        Summary:
            The wraped for python keycloak client to get user infomation
            by email

        Parameter:
            - email(string): the email for target user

        Return:
            - user(dict): the user infomation from keycloak
        """

        user_id = await self.keycloak_admin.get_user_id(username)
        user = await self.keycloak_admin.get_user(user_id)
        return user

    async def update_user_attributes(self, user_id: str, new_attributes: dict) -> dict:
        """
        Summary:
            the function will use keycloak api to update the user attribute
            NOTE HERE: the api update attribute will overwrite existing one.
            so logic now will fetch the existing attributes and update it
            before the request

        Parameter:
            - user_id(string): the user id (hash) in keycloak
            - new_attributes(dictionary): the new attributes that will be ADD
                to the user

        Return:
            newly updated attribute
        """

        user_info = await self.keycloak_admin.get_user(user_id)
        attributes = user_info.get('attributes', {})
        attributes.update(new_attributes)

        async with httpx.AsyncClient() as client:
            api = (
                ConfigSettings.KEYCLOAK_SERVER_URL
                + 'admin/realms/'
                + ConfigSettings.KEYCLOAK_REALM
                + '/users/'
                + user_id
            )
            api_res = await client.put(api, headers=self.header, json={'attributes': attributes})
            if api_res.status_code != 204:
                raise Exception('Fail to update user attributes: ' + str(api_res.__dict__))

        return new_attributes

    async def get_all_users(
        self, username: str = None, email: str = None, first: int = 0, max_users: int = 1000, q: str = ''
    ) -> list:
        """
        Summary:
            The wraped for keycloak api to get all user as
            pagination list that matching the filter condtion

        Parameter:
            - username(string): if payload has username, the api will
                return all user contains target username.
            - email(string): if payload has email, the api will
                return all user contains target email.
            - first(int): the pagination to skip <first> user.
            - max_users(int): the return size of list.
            - q(string): searching the customized user attribute

        Return:
            - users(list): the user infomation from keycloak
        """

        query = {
            'username': username,
            'email': email,
            'first': first,
            'max': max_users,
            'q': q,
        }

        api = ConfigSettings.KEYCLOAK_SERVER_URL + 'admin/realms/' + ConfigSettings.KEYCLOAK_REALM + '/users'
        async with httpx.AsyncClient() as client:
            api_res = await client.get(api, headers=self.header, params=query)
            if api_res.status_code != 200:
                raise Exception('Fail to get all user: ' + str(api_res.__dict__))

        return api_res.json()

    async def get_user_count(
        self, username: str = None, email: str = None, first: int = 0, max_users: int = 1000, q: str = ''
    ) -> int:
        """
        Summary:
            The wraped for keycloak api to get the user count that
            matching the filter condtion

        Parameter:
            - username(string): if payload has username, the api will
                return all user contains target username.
            - email(string): if payload has email, the api will
                return all user contains target email.
            - first(int): the pagination to skip <first> user.
            - max(int): the return size of list.
            - q(string): searching the customized user attribute

        Return:
            - user_count(int)
        """

        query = {
            'username': username,
            'email': email,
            'first': first,
            'max': max_users,
            'q': q,
        }

        api = ConfigSettings.KEYCLOAK_SERVER_URL + 'admin/realms/' + ConfigSettings.KEYCLOAK_REALM + '/users/count'
        async with httpx.AsyncClient() as client:
            api_res = await client.get(api, headers=self.header, params=query)
            if api_res.status_code != 200:
                raise Exception('Fail to get user count: ' + str(api_res.__dict__))
        return api_res.json()

    async def assign_user_role(self, user_id, role_name) -> bytes:
        """
        Summary:
            the function will assign the user to target realm role in keycloak

        Parameter:
            - user_id(string): the user id (hash) in keycloak
            - role_name(string): The new role name that will assign to user

        Return:
            bytes
        """
        realm_roles = await self.keycloak_admin.get_realm_roles()

        find_role = [role for role in realm_roles if role['name'] == role_name]
        if len(find_role) == 0:
            raise Exception('Failed to find the role')

        res = await self.keycloak_admin.assign_realm_roles(user_id=user_id, roles=find_role)
        return res

    async def get_user_realm_roles(self, user_id: str) -> list:
        """
        Summary:
            the function will use the keycloak native api to fecth the
            realm role from user id

        Parameter:
            - user_id(string): the user id (hash) in keycloak

        Return:
            list of the realm roles
        """

        async with httpx.AsyncClient() as client:
            api = (
                ConfigSettings.KEYCLOAK_SERVER_URL
                + 'admin/realms/'
                + ConfigSettings.KEYCLOAK_REALM
                + '/users/'
                + user_id
                + '/role-mappings/realm'
            )
            api_res = await client.get(api, headers=self.header)
            if api_res.status_code != 200:
                raise Exception('Fail to get user realm roles: ' + str(api_res.__dict__))

        return api_res.json()

    async def remove_user_realm_roles(self, user_id: str, realm_roles: list) -> None:
        """
        Summary:
            the function will use the keycloak native api to fecth the
            realm role from user id

        Parameter:
            - user_id(string): the user id (hash) in keycloak

        Return:
            None
        """

        async with httpx.AsyncClient() as client:
            api = (
                ConfigSettings.KEYCLOAK_SERVER_URL
                + 'admin/realms/'
                + ConfigSettings.KEYCLOAK_REALM
                + '/users/'
                + user_id
                + '/role-mappings/realm'
            )
            request = httpx.Request('DELETE', api, headers=self.header, json=realm_roles)
            api_res = await client.send(request)
            if api_res.status_code > 300:
                raise Exception('Fail to remove user from realm: ' + str(api_res.__dict__))

    async def create_project_realm_roles(self, project_roles: list, code: str) -> Response | None:
        """
        Summary:
            the function will use the native the keycloak api to create
            a realm role

        Parameter:
            - project_roles(list): the list of project roles will be admin,
                collaborator, contributor
            - code(string): The project code

        Return:
            None
        """

        for role in project_roles:
            payload = {'name': f'{code}-{role}'}
            url = f'{ConfigSettings.KEYCLOAK_SERVER_URL}admin/realms/{ConfigSettings.KEYCLOAK_REALM}/roles'
            async with httpx.AsyncClient() as client:
                res = await client.post(url=url, headers=self.header, json=payload)
                if res.status_code != 201:
                    raise Exception('Fail to create new role' + str(res.__dict__))
        return res

    async def delete_role_of_user(self, user_id: str, role_name: str):
        """
        Summary:
            the function will use the native the keycloak api to remove
            user from target a realm role

        Parameter:
            - user_id(string): the hash id from keycloak
            - role_name(string): the role name from keycloak

        Return:
            None
        """

        realm_roles = await self.keycloak_admin.get_realm_roles()
        find_role = [role for role in realm_roles if role['name'] == role_name]

        if len(find_role) == 0:
            raise Exception(f'User {user_id} does not have role {role_name}')

        url = f'{ConfigSettings.KEYCLOAK_SERVER_URL}admin/realms/{self.realm_name}/users/{user_id}/role-mappings/realm'
        async with httpx.AsyncClient() as client:
            delete_res = await client.request('DELETE', url, json=find_role, headers=self.header)
        return delete_res

    async def get_users_in_role(self, role_name: str) -> list:
        """
        Summary:
            the function will return the all users under target
            role name

        Parameter:
            - role_name(string): the role name from keycloak

        Return:
            list of user:
                - username
                - attributes
                - email
        """

        async with httpx.AsyncClient() as client:
            api = (
                ConfigSettings.KEYCLOAK_SERVER_URL
                + 'admin/realms/'
                + ConfigSettings.KEYCLOAK_REALM
                + '/roles/'
                + role_name
                + '/users'
            )
            api_res = await client.get(api, headers=self.header)

            if api_res.status_code == 404:
                raise Exception(f'Role {role_name} is not found')

        return api_res.json()

    async def sync_user_trigger(self):
        url = f'{ConfigSettings.KEYCLOAK_SERVER_URL}admin/realms/{ConfigSettings.KEYCLOAK_REALM}/user-storage/{ConfigSettings.KEYCLOAK_ID}/sync?action=triggerChangedUsersSync'  # noqa:E501
        async with httpx.AsyncClient() as client:
            res = await client.post(url=url, headers=self.header)
        return res

    async def get_group_by_name(self, group_name: str) -> dict | None:
        """
        Summary:
            the function will get the group from keycloak

        Parameter:
            - group_name(string): the group name from keycloak

        Return:
            group information(dict)
        """
        groups = await self.keycloak_admin.get_groups({'name': group_name, 'max': 1})
        if groups:
            return groups[0]

    async def create_group(self, group_name: str) -> None:
        """
        Summary:
            the function will create new group in keycloak

        Parameter:
            - group_name(string): the group name from keycloak

        Return:
            None
        """

        group_dict = {'name': group_name}
        await self.keycloak_admin.create_group(group_dict)

    async def add_user_to_group(self, user_id: str, group_id: str) -> None:
        """
        Summary:
            the function will create new group in keycloak

        Parameter:
            - user_id(string): the user id from keycloak
            - group_id(string): the group id from keycloak

        Return:
            None
        """

        await self.keycloak_admin.group_user_add(user_id, group_id)

    async def remove_user_from_group(self, user_id: str, group_id: str) -> None:
        """
        Summary:
            the function will create new group in keycloak

        Parameter:
            - user_id(string): the user id from keycloak
            - group_id(string): the group id from keycloak

        Return:
            None
        """
        await self.keycloak_admin.group_user_remove(user_id, group_id)

    async def check_user_exists(self, email: str) -> bool:
        try:
            await self.get_user_by_email(email)
            return True
        except exceptions.KeycloakGetError:
            return False

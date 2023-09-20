# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import LoggerFactory
from keycloak import KeycloakAdmin

from app import ConfigSettings
from app.models.api_response import EAPIResponseCode
from app.resources.error_handler import APIException

_logger = LoggerFactory('keycloak_client').get_logger()


class KeycloakClient:
    def __init__(self) -> None:
        self.client = None

    async def connect(self) -> None:
        """Establishing a Keycloak connection."""
        try:
            self.client = KeycloakAdmin(
                server_url=ConfigSettings.KEYCLOAK_SERVER_URL,
                client_id=ConfigSettings.KEYCLOAK_CLIENT_ID,
                client_secret_key=ConfigSettings.KEYCLOAK_SECRET,
                realm_name=ConfigSettings.KEYCLOAK_REALM,
                verify=True,
            )
            await self.client.connect()
        except Exception as e:
            error_msg = f'Error connecting to Keycloak: {e}'
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

    def disconnect(self) -> None:
        """This is basically an API wrapper, so no disconnect required."""
        pass

    async def __aenter__(self) -> 'KeycloakClient':
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    @staticmethod
    def format_group_name(group_name: str) -> str:
        return ConfigSettings.LDAP_PREFIX + '-' + group_name

    @staticmethod
    def format_user_data(response: list[dict]) -> list[dict]:
        """Format Keycloak query response data to Pilot."""
        return [
            {
                'username': user.get('username'),
                'id': user.get('id'),
                'email': user.get('email'),
                'first_name': user.get('firstName'),
                'last_name': user.get('lastName'),
                'groups': user.get('groups', []),
            }
            for user in response
        ]

    @staticmethod
    def format_group_data(group: dict) -> dict:
        """Format Keycloak query response data to Pilot."""
        return {
            'group_name': group.get('name'),
            'id': group.get('id'),
            'subgroups': group.get('subGroups', []),
        }

    async def get_user_by_email(self, email: str) -> dict:
        """Query user by email, only one user per query."""
        users = await self.client.get_users({'email': email, 'max': 1})
        if not users:
            error_msg = f'User not found: {email}'
            raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg=error_msg)
        return self.format_user_data(users)[0]

    async def get_user_by_username(self, username: str) -> dict:
        """Query user by username, only one user per query."""
        users = await self.client.get_users({'username': username, 'max': 1})
        if not users:
            error_msg = f'User not found: {username}'
            raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg=error_msg)
        return self.format_user_data(users)[0]

    async def get_group_by_name(self, group_name: str) -> dict:
        """Query for group by name."""
        group = await self.client.get_group_by_path(path=f'/{group_name}')
        if group is None:
            error_msg = f'Group not found: {group_name}'
            raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg=error_msg)
        return self.format_group_data(group)

    async def add_user_to_group(self, email: str, group_name: str) -> str:
        """Add user to the specified group."""
        user = await self.get_user_by_email(email)
        group = await self.get_group_by_name(group_name)
        await self.client.group_user_add(user_id=user['id'], group_id=group['id'])
        return 'success'

    async def remove_user_from_group(self, email: str, group_name: str) -> str:
        """Remove user from the specified group."""
        user = await self.get_user_by_email(email)
        group = await self.get_group_by_name(group_name)
        await self.client.group_user_remove(user_id=user['id'], group_id=group['id'])
        return 'success'

    async def create_group(self, group_name: str, description: str = '') -> str:
        """Create a group with given name."""
        group = await self.client.create_group(payload={'name': group_name}, skip_exists=True)
        if group:
            return group
        else:
            error_msg = f'Could not create a group {group_name}'
            raise APIException(status_code=EAPIResponseCode.bad_request.value, error_msg=error_msg)

    async def delete_group(self, group_name: str) -> str:
        """Delete a group."""
        group = await self.get_group_by_name(group_name)
        await self.client.delete_group(group['id'])
        return 'success'

    async def create_user(self, username: str, email: str, first_name: str, last_name: str, password: str) -> dict:
        """Create a user with given parameters."""
        if user := await self.client.create_user(
            {
                'email': email,
                'username': username,
                'enabled': True,
                'firstName': first_name,
                'lastName': last_name,
                'credentials': [
                    {
                        'value': password,
                        'type': 'password',
                    }
                ],
            }
        ):
            return user
        else:
            error_msg = f'Could not create a user {username}'
            raise APIException(status_code=EAPIResponseCode.bad_request.value, error_msg=error_msg)

    async def user_exists(self, email: str) -> bool:
        try:
            await self.get_user_by_email(email)
        except Exception:
            return False
        return True

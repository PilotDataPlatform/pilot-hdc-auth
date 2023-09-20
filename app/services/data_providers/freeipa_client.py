# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import random
import string

from common import LoggerFactory
from python_freeipa import ClientMeta
from python_freeipa.exceptions import DuplicateEntry
from python_freeipa.exceptions import Unauthorized

from app.config import ConfigSettings
from app.models.api_response import EAPIResponseCode
from app.resources.error_handler import APIException

_logger = LoggerFactory('freeipa_client').get_logger()


class FreeIPAClient:
    def __init__(self) -> None:
        self.client = None

    def connect(self) -> None:
        try:
            self.client = ClientMeta(ConfigSettings.FREEIPA_URL, verify_ssl=False)
            self.client.login(ConfigSettings.FREEIPA_USERNAME, ConfigSettings.FREEIPA_PASSWORD)
        except Unauthorized as e:
            msg = f'Failed to log into FreeIPA: {e}'
            _logger.error(msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=msg)
        except Exception as e:
            msg = f'Error connecting to FreeIPA: {e}'
            _logger.error(msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=msg)

    def disconnect(self) -> None:
        pass

    async def __aenter__(self) -> 'FreeIPAClient':
        self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    async def add_user_to_group(self, email: str, group_name: str) -> str:
        user = await self.get_user_by_email(email)
        await self.client.group_add_member(
            a_cn=group_name,
            o_user=user['username'],
        )

    async def remove_user_from_group(self, email: str, group_name: str) -> str:
        user = await self.get_user_by_email(email)
        await self.client.group_remove_member(
            a_cn=group_name,
            o_user=user['username'],
        )

    async def get_user_by_email(self, email: str) -> dict:
        user = await self.client.user_find(o_mail=email)
        if not user['result']:
            raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg=f'User not found: {email}')
        return {
            'username': user['result'][0]['uid'],
            'email': user['result'][0]['mail'],
            'first_name': user['result'][0]['givenname'],
            'last_name': user['result'][0]['sn'],
            'groups': user['result'][0]['memberof_group'],
        }

    async def get_user_by_username(self, username: str) -> dict:
        user = await self.client.user_find(
            o_uid=username,
        )
        if not user['result']:
            raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg=f'User not found: {username}')
        return {
            'username': user['result'][0]['uid'],
            'email': user['result'][0]['mail'],
            'first_name': user['result'][0]['givenname'],
            'last_name': user['result'][0]['sn'],
            'groups': user['result'][0]['memberof_group'],
        }

    async def create_group(self, group_name: str, description: str = '') -> str:
        await self.client.group_add(
            a_cn=group_name,
            o_description=description,
        )

    async def delete_group(self, group_name: str) -> str:
        await self.client.group_del(
            a_cn=group_name,
        )

    async def create_user(self, username: str, email: str, first_name: str, last_name: str, password: str) -> dict:
        try:
            temp_password = ''.join(random.choice(string.ascii_lowercase) for i in range(12))
            user = await self.client.user_add(
                a_uid=username,
                o_givenname=first_name,
                o_sn=last_name,
                o_cn=first_name + ' ' + last_name,
                o_mail=email,
                o_userpassword=temp_password,
            )
            await self.client.change_password(username, password, temp_password)
        except DuplicateEntry as e:
            _logger.error(f'Duplicate user in create FreeIPA user: {e}')
            raise APIException(status_code=EAPIResponseCode.conflict.value, error_msg=f'User already exists: {e}')

        return {
            'username': user['result']['uid'][0],
            'email': user['result']['mail'][0],
            'first_name': user['result']['givenname'][0],
            'last_name': user['result']['sn'][0],
        }

    async def user_exists(self, email: str) -> bool:
        try:
            await self.get_user_by_email(email)
        except Exception:
            return False
        return True

    def format_group_name(self, group_name: str) -> str:
        return ConfigSettings.LDAP_PREFIX + '-' + group_name

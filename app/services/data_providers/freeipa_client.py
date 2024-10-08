# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import random
import secrets
import string

from fastapi import Depends
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from python_freeipa import ClientMeta
from python_freeipa.exceptions import DuplicateEntry
from python_freeipa.exceptions import FreeIPAError
from python_freeipa.exceptions import PWChangeInvalidPassword
from python_freeipa.exceptions import PWChangePolicyError
from python_freeipa.exceptions import Unauthorized

from app.config import ConfigSettings
from app.config import get_settings
from app.logger import logger
from app.models.api_response import EAPIResponseCode
from app.resources.error_handler import APIException


class FreeIPAException(Exception):
    """Raised when any unexpected behaviour occurred while making requests to FreeIPA."""


class FreeIPAClient:
    def __init__(self, settings: ConfigSettings) -> None:
        self.client = None
        self.freeipa_url = settings.FREEIPA_URL
        self.freeipa_username = settings.FREEIPA_USERNAME
        self.freeipa_password = settings.FREEIPA_PASSWORD

    def connect(self) -> None:
        try:
            self.client = ClientMeta(self.freeipa_url, verify_ssl=False)
            self.client.login(self.freeipa_username, self.freeipa_password)
        except Unauthorized as e:
            msg = f'Failed to log into FreeIPA: {e}'
            logger.error(msg)
            raise HTTPException(status_code=401, detail=msg)
        except Exception as e:
            msg = f'Error connecting to FreeIPA: {e}'
            logger.error(msg)
            raise HTTPException(status_code=500, detail=msg)

    def disconnect(self) -> None:
        pass

    async def __aenter__(self) -> 'FreeIPAClient':
        await run_in_threadpool(self.connect)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    async def add_user_to_group(self, email: str, group_name: str) -> str:
        logger.info(f'Adding user "{email}" to group "{group_name}"')
        user = await self.get_user_by_email(email)
        await run_in_threadpool(
            self.client.group_add_member,
            a_cn=group_name,
            o_user=user['username'],
        )

    async def remove_user_from_group(self, email: str, group_name: str) -> str:
        user = await self.get_user_by_email(email)
        await run_in_threadpool(
            self.client.group_remove_member,
            a_cn=group_name,
            o_user=user['username'],
        )

    async def get_hbac_rule_by_name(self, name: str):
        hbac_rule = await run_in_threadpool(self.client.hbacrule_find, a_criteria=name, o_sizelimit=1)
        if hbac_rule['count'] < 1:
            message = f'HBAC rule with name {name} was not found'
            logger.warning(message)
            raise HTTPException(status_code=404, detail=message)
        else:
            return {
                'name': hbac_rule['result'][0]['cn'][0],
                'description': hbac_rule['result'][0]['description'][0],
                'members': hbac_rule['result'][0]['memberuser_user'],
                'dn': hbac_rule['result'][0]['dn'],
            }

    async def add_user_to_hbac_rule(self, username: str, hbac_rule: str) -> None:
        user = await self.get_user_by_username(username)
        logger.info(f'Adding user {user["username"]} to HBAC rule {hbac_rule}')

        await run_in_threadpool(
            self.client.hbacrule_add_user,
            a_cn=hbac_rule,
            o_user=user['username'],
        )

    async def remove_user_from_hbac_rule(self, username: str, hbac_rule: str) -> None:
        user = await self.get_user_by_username(username)
        logger.info(f'Removing user {user["username"]} from HBAC rule {hbac_rule}')

        await run_in_threadpool(
            self.client.hbacrule_remove_user,
            a_cn=hbac_rule,
            o_user=user['username'],
        )

    async def get_user_by_email(self, email: str) -> dict:
        user = await run_in_threadpool(self.client.user_find, o_mail=email)
        if not user['result']:
            raise HTTPException(status_code=404, detail=f'User not found: {email}')
        return {
            'username': user['result'][0]['uid'][0],
            'email': user['result'][0]['mail'][0],
            'first_name': user['result'][0]['givenname'][0],
            'last_name': user['result'][0]['sn'][0],
            'groups': user['result'][0]['memberof_group'],
            'hbac_rules': user['result'][0].get('memberof_hbacrule', []),
        }

    async def get_user_by_username(self, username: str) -> dict:
        user = await run_in_threadpool(
            self.client.user_find,
            o_uid=username,
        )
        if not user['result']:
            message = f'User not found: {username}'
            logger.error(message)
            raise HTTPException(status_code=404, detail=message)
        return {
            'username': user['result'][0]['uid'][0],
            'email': user['result'][0]['mail'][0],
            'first_name': user['result'][0]['givenname'][0],
            'last_name': user['result'][0]['sn'][0],
            'groups': user['result'][0]['memberof_group'],
            'hbac_rules': user['result'][0].get('memberof_hbacrule', []),
        }

    async def create_group(self, group_name: str, description: str = '') -> str:
        await run_in_threadpool(
            self.client.group_add,
            a_cn=group_name,
            o_description=description,
        )

    async def delete_group(self, group_name: str) -> str:
        await run_in_threadpool(
            self.client.group_del,
            a_cn=group_name,
        )

    async def create_user(self, username: str, email: str, first_name: str, last_name: str, password: str) -> dict:
        try:
            temp_password = ''.join(random.choice(string.ascii_lowercase) for i in range(12))
            user = self.client.user_add(
                a_uid=username,
                o_givenname=first_name,
                o_sn=last_name,
                o_cn=first_name + ' ' + last_name,
                o_mail=email,
                o_userpassword=temp_password,
            )
            await run_in_threadpool(self.client.change_password, username, password, temp_password)
        except DuplicateEntry:
            message = f'Tried to create duplicate user in FreeIPA with username {username}'
            logger.error(message)
            raise HTTPException(status_code=409, detail=message)
        except FreeIPAError as e:
            message = f'Error while trying to create user {username}: {e.message}'
            logger.error(message)
            raise HTTPException(status_code=500, detail=message)

        return {
            'username': user['result']['uid'][0],
            'email': user['result']['mail'][0],
            'first_name': user['result']['givenname'][0],
            'last_name': user['result']['sn'][0],
            'groups': user['result'].get('memberof_group', []),
            'hbac_rules': user['result'].get('memberof_hbacrule', []),
        }

    async def user_exists(self, email: str) -> bool:
        try:
            await self.get_user_by_email(email)
        except Exception:
            return False
        return True

    def format_group_name(self, group_name: str) -> str:
        return ConfigSettings.LDAP_PREFIX + '-' + group_name

    async def change_password(self, username: str, new_password: str, old_password: str) -> None:
        """Change password in FreeIPA."""
        try:
            result = await run_in_threadpool(self.client.change_password, username, new_password, old_password)
        except PWChangeInvalidPassword:
            logger.exception('Bad current password in FreeIPA')
            raise APIException(status_code=EAPIResponseCode.forbidden.value, error_msg='Permission Denied')
        except PWChangePolicyError:
            logger.exception('Password Policy error in FreeIPA')
            raise APIException(
                status_code=EAPIResponseCode.conflict.value, error_msg='Password Policy error in FreeIPA'
            )
        return result

    async def reset_password(self, username: str, new_password: str) -> None:
        """Change password in FreeIPA."""
        try:
            temp_password = secrets.token_hex(32)
            args = [
                username,
                temp_password,
            ]
            # When an admin sets a new password FreeIPA expires it and makes the user change it, to get around this and
            # set a non-expired password for the user we set it and then change it
            await run_in_threadpool(self.client._request, 'passwd', args)
            result = await run_in_threadpool(self.client.change_password, username, new_password, temp_password)
        except FreeIPAError as e:
            message = f'Error while trying to reset password for user {username}: {e.message}'
            logger.error(message)
            raise HTTPException(status_code=500, detail=message)
        return result


def get_freeipa_client(settings: ConfigSettings = Depends(get_settings)) -> FreeIPAClient:
    """Get auth service client as a FastAPI dependency."""

    return FreeIPAClient(settings=settings)

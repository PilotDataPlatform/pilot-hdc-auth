# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import time as tm
from enum import Enum
from http import HTTPStatus
from typing import Any
from typing import Mapping
from typing import Optional
from uuid import UUID

from httpx import AsyncClient
from httpx import AsyncHTTPTransport
from httpx import HTTPStatusError
from httpx import Response

from app.components.exceptions import NotFound
from app.components.keycloak.models import Role
from app.components.keycloak.models import User


class GrantTypes(str, Enum):
    """Available grant types.

    https://auth0.com/docs/get-started/applications/application-grant-types#available-grant-types
    """

    CLIENT_CREDENTIALS = 'client_credentials'

    def __str__(self) -> str:
        return str(self.value)


class KeycloakClient:
    """Client for Keycloak API."""

    def __init__(
        self,
        *,
        server_url: str,
        realm: str,
        client_id: str,
        client_secret: str,
        grant_type: list[GrantTypes],
        timeout: int = 10,
        retries: int = 1,
    ) -> None:
        self.server_url = server_url.rstrip('/')
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.grant_type = grant_type

        self.access_token = 'missing'
        self.access_token_expiration = 0
        self.client = AsyncClient(timeout=timeout, transport=AsyncHTTPTransport(retries=retries))

    @property
    def headers(self) -> dict[str, Any]:
        return {
            'Authorization': f'Bearer {self.access_token}',
        }

    @property
    def is_authorization_expiring_soon(self) -> bool:
        """Check if access token is about to expire in the next 10 seconds."""

        return int(tm.monotonic()) >= (self.access_token_expiration - 10)

    async def _request(
        self, method: str, path: str, json: Optional[Any] = None, params: Optional[Mapping[str, Any]] = None
    ) -> Response:
        """Make http request.

        If token expires, it will be refreshed and request will be retried.
        """

        url = f'{self.server_url}/{path}'

        try:
            response = await self.client.request(method, url, json=json, params=params, headers=self.headers)
            if response.status_code != HTTPStatus.UNAUTHORIZED:
                response.raise_for_status()
                return response

            await self.authorize()

            response = await self.client.request(method, url, json=json, params=params, headers=self.headers)
            response.raise_for_status()
            return response
        except HTTPStatusError as e:
            if e.response.status_code == HTTPStatus.NOT_FOUND:
                raise NotFound
            raise e

    async def _get(self, path: str, params: Optional[Mapping[str, Any]] = None) -> Response:
        """Send GET request."""

        return await self._request('GET', path, params=params)

    async def authorize(self) -> None:
        """Request access token using client credentials."""

        url = f'{self.server_url}/realms/{self.realm}/protocol/openid-connect/token'
        data = {
            'scope': 'openid',
            'grant_type': self.grant_type,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        response = await self.client.post(url, data=data)
        response.raise_for_status()
        auth = response.json()

        self.access_token = auth['access_token']
        self.access_token_expiration = int(tm.monotonic()) + auth['expires_in']

    async def get_user(self, user_id: UUID) -> User:
        """Retrieve user by id."""

        url = f'admin/realms/{self.realm}/users/{user_id}'
        response = await self._get(url)

        user = response.json()

        return User(user)

    async def get_user_by_username(self, username: str) -> User:
        """Retrieve first user by exact match of username."""

        url = f'admin/realms/{self.realm}/users'
        params = {'username': username, 'exact': 'true'}
        response = await self._get(url, params=params)
        users = response.json()

        try:
            user = users.pop(0)
            return User(user)
        except IndexError:
            raise NotFound

    async def get_user_roles(self, user_id: UUID) -> list[Role]:
        """Retrieve list of user roles."""

        url = f'admin/realms/{self.realm}/users/{user_id}/role-mappings/realm'
        response = await self._get(url)
        roles = response.json()

        return [Role(role) for role in roles]

# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

import pytest
from faker import Faker

from app.components.exceptions import NotFound
from app.components.keycloak.client import KeycloakClient
from app.components.keycloak.models import Role
from app.components.keycloak.models import User


class KeycloakClientMock(KeycloakClient):
    """Mock of keycloak client class for creating testing purpose entries."""

    fake: Faker

    def __init__(self, fake: Faker) -> None:
        super().__init__(server_url='', realm='', client_id='', client_secret='', grant_type=[])

        self.fake = fake

        self._users = {}
        self._user_roles = {}

    def create_user(self, *, id_: UUID = ..., username: str = ..., email: str = ..., is_disabled: bool = ...) -> User:
        if id_ is ...:
            id_ = self.fake.uuid4(None)

        if username is ...:
            username = self.fake.unique.user_name().lower()

        if email is ...:
            email = self.fake.unique.email()

        status = ['active']
        if is_disabled is True:
            status = ['disabled']

        attributes = {'status': status}
        user = User({'id': str(id_), 'username': username, 'email': email, 'attributes': attributes})

        self._users[user.id] = user

        return user

    def create_role(self, *, user_id: UUID, name: str = ...) -> Role:
        if name is ...:
            name = self.fake.word()

        role = Role({'id': self.fake.uuid4(), 'name': name})

        self._user_roles.setdefault(user_id, []).append(role)

        return role

    async def authorize(self) -> None:
        pass

    async def get_user_by_username(self, username: str) -> User:
        users = {user.username: user for user in self._users.values()}
        try:
            return users[username]
        except KeyError:
            raise NotFound

    async def get_user_roles(self, user_id: UUID) -> list[Role]:
        return self._user_roles.get(user_id, [])


@pytest.fixture
def keycloak_client_mock(fake) -> KeycloakClientMock:
    yield KeycloakClientMock(fake)


@pytest.fixture
def keycloak_client(httpserver, fake) -> KeycloakClient:
    yield KeycloakClient(
        server_url=httpserver.url_for('/'), realm=fake.word(), client_id='', client_secret='', grant_type=[]
    )

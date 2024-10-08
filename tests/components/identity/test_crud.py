# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

import pytest

from app.components.identity.crud import IdentityCRUD
from app.resources.keycloak_api.ops_admin import OperationsAdmin


class TestIdentityCRUD:
    async def test_create_operations_admin_returns_an_instance_of_operations_admin_class_with_proper_headers(
        self, keycloak_client, fake
    ):
        keycloak_client.access_token = fake.pystr()
        keycloak_client.access_token_expiration = 2**100
        expected_headers = {
            'Authorization': f'Bearer {keycloak_client.access_token}',
            'Content-Type': 'application/json',
        }
        identity_crud = IdentityCRUD(keycloak_client)

        admin_client = await identity_crud.create_operations_admin()

        assert isinstance(admin_client, OperationsAdmin) is True
        assert admin_client.header == expected_headers
        assert admin_client.keycloak_admin.connection.headers == expected_headers

    async def test_get_user_by_username_returns_user_by_username(self, keycloak_client_mock, identity_crud):
        created_user = keycloak_client_mock.create_user()

        received_user = await identity_crud.get_user_by_username(created_user['username'])

        assert received_user == created_user

    async def test_get_user_by_username_returns_none_when_user_not_found(self, identity_crud):
        received_user = await identity_crud.get_user_by_username('non-existing')

        assert received_user is None

    @pytest.mark.parametrize('user_id_type', [str, UUID])
    async def test_get_user_realm_roles_returns_list_of_user_roles(
        self, user_id_type, keycloak_client_mock, identity_crud, fake
    ):
        user_id = fake.uuid4(str)
        created_role = keycloak_client_mock.create_role(user_id=UUID(user_id))

        received_roles = await identity_crud.get_user_realm_roles(user_id_type(user_id))

        assert received_roles == [created_role]

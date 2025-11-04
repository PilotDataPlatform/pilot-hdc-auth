# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

from keycloak import ConnectionManager
from keycloak import KeycloakAdmin

from app.components.exceptions import NotFound
from app.components.keycloak.client import KeycloakClient
from app.components.keycloak.models import Role
from app.components.keycloak.models import User
from app.resources.keycloak_api.ops_admin import OperationsAdmin


class IdentityCRUD:
    """CRUD for managing user accounts."""

    keycloak_client: KeycloakClient

    def __init__(self, keycloak_client: KeycloakClient) -> None:
        self.keycloak_client = keycloak_client

    async def create_operations_admin(self) -> OperationsAdmin:
        """Return an instance of legacy OperationsAdmin class for backward compatibility."""

        if self.keycloak_client.is_authorization_expiring_soon:
            await self.keycloak_client.authorize()

        server_url = f'{self.keycloak_client.server_url}/'
        realm_name = self.keycloak_client.realm
        headers = self.keycloak_client.headers | {'Content-Type': 'application/json'}
        keycloak_admin = KeycloakAdmin(server_url=server_url, realm_name=realm_name)
        keycloak_admin.connection = ConnectionManager(
            base_url=server_url, headers=headers, timeout=self.keycloak_client.client.timeout
        )
        operations_admin = OperationsAdmin(keycloak_admin=keycloak_admin, realm_name=realm_name, headers=headers)

        return operations_admin

    async def get_user_by_username(self, username: str) -> User | None:
        try:
            return await self.keycloak_client.get_user_by_username(username)
        except NotFound:
            return None

    async def get_user_realm_roles(self, user_id: UUID | str) -> list[Role]:
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        return await self.keycloak_client.get_user_roles(user_id)

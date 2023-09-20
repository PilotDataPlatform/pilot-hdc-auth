# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from keycloak import KeycloakOpenID

from app.config import ConfigSettings


class OperationsUser:
    @classmethod
    async def create(self, client_id: str, realm_name: str, client_secret_key: str) -> None:
        self = OperationsUser()
        self.keycloak_openid = KeycloakOpenID(
            server_url=ConfigSettings.KEYCLOAK_SERVER_URL,
            client_id=client_id,
            realm_name=realm_name,
            client_secret_key=client_secret_key,
        )
        self.config_well_know = await self.keycloak_openid.well_known()
        self.token = {}
        return self

    async def get_token(self, username: str, password: str) -> dict:
        self.token = await self.keycloak_openid.token(username, password)
        return self.token

    async def get_userinfo(self) -> dict:
        userinfo = await self.keycloak_openid.userinfo(self.token['access_token'])
        return userinfo

    async def get_refresh_token(self, token: str) -> dict:
        self.token = await self.keycloak_openid.refresh_token(token)
        return self.token

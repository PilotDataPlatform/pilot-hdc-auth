# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends

from app.components.keycloak.client import GrantTypes
from app.components.keycloak.client import KeycloakClient
from app.config import Settings
from app.config import get_settings


class GetKeycloakClient:
    """Create a FastAPI callable dependency for KeycloakClient single instance."""

    def __init__(self) -> None:
        self.instance = None

    async def __call__(self, settings: Settings = Depends(get_settings)) -> KeycloakClient:
        """Return an instance of KeycloakClient class."""

        if not self.instance:
            self.instance = KeycloakClient(
                server_url=settings.KEYCLOAK_SERVER_URL,
                realm=settings.KEYCLOAK_REALM,
                client_id=settings.KEYCLOAK_CLIENT_ID,
                client_secret=settings.KEYCLOAK_SECRET,
                grant_type=[GrantTypes.CLIENT_CREDENTIALS],
                timeout=settings.SERVICE_CLIENT_TIMEOUT,
            )
            await self.instance.authorize()

        return self.instance


get_keycloak_client = GetKeycloakClient()

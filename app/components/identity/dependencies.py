# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends

from app.components.identity.crud import IdentityCRUD
from app.components.keycloak.client import KeycloakClient
from app.components.keycloak.dependencies import get_keycloak_client


def get_identity_crud(keycloak_client: KeycloakClient = Depends(get_keycloak_client)) -> IdentityCRUD:
    """Return an instance of IdentityCRUD as a dependency."""

    return IdentityCRUD(keycloak_client)

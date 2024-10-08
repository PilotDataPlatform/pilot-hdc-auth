# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest

from app.components.identity.crud import IdentityCRUD


@pytest.fixture
def identity_crud(keycloak_client_mock) -> IdentityCRUD:
    yield IdentityCRUD(keycloak_client_mock)

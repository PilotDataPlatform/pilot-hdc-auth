# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest


@pytest.mark.parametrize('set_identity_backend', ['freeipa', 'openldap', 'keycloak'], indirect=True)
def test_create_user(test_client, mocker, set_identity_backend, identity_client_mock):
    response = test_client.post(
        '/v1/admin/users',
        json={
            'username': 'test',
            'email': 'test@test.com',
            'password': '1234',
            'first_name': 'Test',
            'last_name': 'Testing',
        },
    )
    assert response.status_code == 200

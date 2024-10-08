# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from uuid import UUID

from common import ProjectClient

from app.config import ConfigSettings
from app.resources.keycloak_api.ops_admin import OperationsAdmin
from tests.conftest import TEST_USER
from tests.conftest import FakeProjectObject


def test_project_role_change_200(test_client, mocker, httpx_mock, keycloak_admin_mock, keycloak_client_mock):
    operator = 'admin'
    keycloak_client_mock.create_user(username=operator)
    keycloak_client_mock.create_role(user_id=UUID(TEST_USER['id']), name='indoctestproject-collaborator')
    httpx_mock.add_response(method='POST', url=ConfigSettings.NOTIFY_SERVICE + 'all/notifications/', status_code=204)
    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())

    url = re.compile(
        '^http://keycloakadmin/realms//users/.*/role-mappings/realm$',
    )
    httpx_mock.add_response(method='DELETE', url=url, json={})

    response = test_client.put(
        '/v1/user/project-role',
        json={
            'email': 'test_user@test.com',
            'project_role': 'indoctestproject-admin',
            'operator': operator,
            'project_code': 'test_project',
        },
    )
    assert response.status_code == 200


def test_project_role_change_keycloak_exception_500(test_client, mocker, httpx_mock):
    mocker.patch.object(OperationsAdmin, '__init__', side_effect=Exception)
    response = test_client.put(
        '/v1/user/project-role',
        json={
            'email': 'test_user@test.com',
            'project_role': 'indoctestproject-admin',
            'operator': 'admin',
            'project_code': 'test_project',
        },
    )
    assert response.status_code == 500


def test_project_role_change_notification_error_500(
    test_client, mocker, httpx_mock, keycloak_admin_mock, keycloak_client_mock
):
    operator = 'admin'
    keycloak_client_mock.create_user(username=operator)
    keycloak_client_mock.create_role(user_id=UUID(TEST_USER['id']), name='indoctestproject-collaborator')
    httpx_mock.add_response(
        method='POST', url=ConfigSettings.NOTIFY_SERVICE + 'all/notifications/', status_code=500, json={}
    )
    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())

    url = re.compile(
        '^http://keycloakadmin/realms//users/.*/role-mappings/realm$',
    )
    httpx_mock.add_response(method='DELETE', url=url, json={})

    response = test_client.put(
        '/v1/user/project-role',
        json={
            'email': 'test_user@test.com',
            'project_role': 'indoctestproject-admin',
            'operator': operator,
            'project_code': 'test_project',
        },
    )
    assert response.status_code == 500

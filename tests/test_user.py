# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from uuid import uuid4

from common import ProjectClient
from keycloak import exceptions

from app.resources.keycloak_api.ops_user import OperationsUser
from tests.conftest import FakeProjectObject

test_user = {
    'username': 'test_user',
    'email': 'test_user',
    'id': 'test_user',
    'firstName': 'firstName',
    'lastName': 'lastName',
    'attributes': {'status': ['active']},
}


def test_authentication(test_client, mocker, keycloak_admin_mock, httpx_mock, keycloak_client_mock):
    keycloak_client_mock.create_user(username=test_user['username'])
    url = re.compile(
        'http://keycloakadmin/realms//users/.*$',
    )
    httpx_mock.add_response(method='PUT', url=url, status_code=204)
    response = test_client.post('/v1/users/auth', json={'username': 'test_user', 'password': 'test_user'})
    assert response.status_code == 200


def test_authentication_for_disabled_user_returns_unauthorized_response(
    test_client, keycloak_admin_mock, keycloak_client_mock
):
    keycloak_client_mock.create_user(username=test_user['username'], is_disabled=True)

    response = test_client.post('/v1/users/auth', json={'username': 'test_user', 'password': 'test_user'})
    assert response.status_code == 401
    assert response.json().get('error_msg') == 'User is disabled'


def test_authentication_with_password_returns_unauthorized_response_when_get_token_fails(test_client, mocker):
    mocker.patch('app.resources.keycloak_api.ops_user.OperationsUser.create', return_value=OperationsUser())
    mocker.patch(
        'app.resources.keycloak_api.ops_user.OperationsUser.get_token',
        side_effect=exceptions.KeycloakAuthenticationError,
    )

    response = test_client.post('/v1/users/auth', json={'username': 'test_user', 'password': 'test_user'})
    assert response.status_code == 401


def test_authentication_with_password_returns_not_found_response_when_get_user_by_username_fails(
    test_client, mocker, keycloak_admin_mock
):
    mocker.patch(
        'app.components.identity.crud.IdentityCRUD.get_user_by_username', side_effect=exceptions.KeycloakGetError
    )

    response = test_client.post('/v1/users/auth', json={'username': 'test_user', 'password': 'test_user'})
    assert response.status_code == 404


def test_token_refresh(test_client, mocker, keycloak_admin_mock):
    response = test_client.post(
        '/v1/users/refresh',
        json={
            'refreshtoken': 'test_token',
        },
    )
    assert response.status_code == 200


def test_token_refresh_missing_payload(test_client, mocker, keycloak_admin_mock):
    response = test_client.post('/v1/users/refresh', json={})
    assert response.status_code == 422


def test_add_user_keycloak_realm_role(test_client, mocker, keycloak_admin_mock, httpx_mock):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_email',
        return_value={'id': 'test', 'username': 'test'},
    )
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.assign_user_role', return_value={})

    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())

    response = test_client.post('/v1/user/project-role', json={'email': 'test_email', 'project_role': 'test_project'})
    assert response.status_code == 200


def test_remove_user_keycloak_realm_role(test_client, mocker, keycloak_admin_mock, keycloak_client_mock):
    operator = 'admin'
    keycloak_client_mock.create_user(username=operator)
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_email',
        return_value={'id': uuid4(), 'username': 'fakeuser'},
    )
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_username',
        return_value={'id': uuid4(), 'username': 'fakeuser'},
    )
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_realm_roles', return_value=[])
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.delete_role_of_user', return_value={})
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.assign_user_role', return_value=None)

    response = test_client.delete(
        '/v1/user/project-role',
        params={
            'email': 'test_email',
            'project_role': 'test_project',
            'operator': operator,
            'project_code': 'fakecoderemove',
        },
    )
    assert response.status_code == 200


def create_test_user_list(size=10):
    user_list = []
    for x in range(size):
        user_list.append(
            {
                'username': f'test_user_{x:d}',
                'email': f'test_user_{x:d}@email.com',
                'id': f'test_user_{x:d}',
                'firstName': f'firstName_{x:d}',
                'lastName': f'lastName_{x:d}',
                'attributes': {'status': ['active']},
            }
        )

    return user_list


def test_list_platform_user_pagination_1(test_client, mocker, keycloak_admin_mock):
    num_of_user = 20
    page_size = 10
    users = create_test_user_list(num_of_user)

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_count', return_value=len(users))
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_all_users', return_value=users)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role', return_value=[])

    response = test_client.get('/v1/users', params={'page_size': page_size})
    assert response.status_code == 200
    assert len(response.json().get('result')) == page_size


def test_list_platform_user_pagination_2(test_client, mocker, keycloak_admin_mock):
    num_of_user = 20
    page_size = 5
    users = create_test_user_list(num_of_user)

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_count', return_value=len(users))
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_all_users', return_value=users)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role', return_value=[])

    response = test_client.get('/v1/users', params={'page_size': page_size})
    assert response.status_code == 200
    assert len(response.json().get('result')) == page_size
    assert response.json().get('num_of_pages') == (num_of_user / page_size)


def test_list_platform_user_platform_admin_check(test_client, mocker, keycloak_admin_mock):
    num_of_user = 20
    users = create_test_user_list(num_of_user)

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_count', return_value=len(users))
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_all_users', return_value=users)
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role',
        return_value=[{'username': 'test_user_1'}],
    )

    response = test_client.get('/v1/users', params={})
    assert response.status_code == 200
    for x in response.json().get('result'):
        if x.get('username') == 'test_user_1':
            assert x.get('role') == 'admin'


def test_list_users_under_roles_filter_order_by_email(test_client, mocker, keycloak_admin_mock):
    num_of_user = 20
    users = create_test_user_list(num_of_user)

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_count', return_value=len(users))
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_all_users', return_value=users)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role', return_value=[])

    response = test_client.get('/v1/users', params={'order_by': 'email', 'order_type': 'desc'})
    assert response.status_code == 200
    user_list = response.json().get('result')
    assert user_list[0].get('email') > user_list[1].get('email')


def test_list_users_under_roles_filter_order_by_username(test_client, mocker, keycloak_admin_mock):
    num_of_user = 20
    users = create_test_user_list(num_of_user)

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_count', return_value=len(users))
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_all_users', return_value=users)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role', return_value=[])

    response = test_client.get('/v1/users', params={'order_by': 'username', 'order_type': 'desc'})
    assert response.status_code == 200
    user_list = response.json().get('result')
    assert user_list[0].get('email') > user_list[1].get('email')


def test_list_users_under_roles_filter_order_by_last_name(test_client, mocker, keycloak_admin_mock):
    num_of_user = 20
    users = create_test_user_list(num_of_user)

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_count', return_value=len(users))
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_all_users', return_value=users)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role', return_value=[])

    response = test_client.get('/v1/users', params={'order_by': 'last_name', 'order_type': 'desc'})
    assert response.status_code == 200
    user_list = response.json().get('result')
    assert user_list[0].get('last_name') > user_list[1].get('last_name')

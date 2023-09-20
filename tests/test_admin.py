# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from uuid import UUID

import pytest
from keycloak import exceptions

from tests.conftest import TEST_USER

test_user = {
    'username': 'test_user',
    'email': 'test_user@test.com',
    'id': '00000000-0000-0000-0000-b8b12239a8ed',
    'firstName': 'firstName',
    'lastName': 'lastName',
    'attributes': {'status': ['active']},
}


def test_get_user_info_by_id(test_client, keycloak_admin_mock):
    response = test_client.get('/v1/admin/user', params={'user_id': 'test_user'})
    assert response.status_code == 200


def test_get_user_info_by_username(test_client, keycloak_client_mock):
    keycloak_client_mock.create_user(username=test_user['username'])

    response = test_client.get('/v1/admin/user', params={'username': 'test_user'})
    assert response.status_code == 200


def test_get_user_info_by_email(test_client, mocker, keycloak_admin_mock):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_email', return_value=test_user.copy()
    )
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_realm_roles', return_value=[])

    response = test_client.get('/v1/admin/user', params={'email': 'test_user@test.com'})
    assert response.status_code == 200


def test_get_user_with_admin_role(test_client, keycloak_admin_mock, keycloak_client_mock):
    keycloak_client_mock.create_role(user_id=UUID(TEST_USER['id']), name='platform-admin')
    response = test_client.get('/v1/admin/user', params={'email': 'test_user@test.com'})
    assert response.status_code == 200
    assert response.json().get('result', {}).get('role') == 'admin'


def test_get_user_with_member_role(test_client, mocker, keycloak_admin_mock):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_email', return_value=test_user.copy()
    )
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_realm_roles',
        return_value=[{'name': 'not-admin'}],
    )

    response = test_client.get('/v1/admin/user', params={'email': 'test_user@test.com'})
    assert response.status_code == 200
    assert response.json().get('result', {}).get('role') == 'member'


def test_get_user_info_missing_params(test_client, keycloak_admin_mock):
    response = test_client.get('/v1/admin/user')
    assert response.status_code == 400
    assert response.json().get('error_msg') == 'One of email, username, user_id is mandetory'


def test_get_user_info_user_not_found(test_client, mocker):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_id', side_effect=exceptions.KeycloakGetError
    )

    response = test_client.get('/v1/admin/user', params={'user_id': 'test_user'})
    assert response.status_code == 404
    assert response.json().get('error_msg') == 'user not found'


def test_update_user_attribute2(test_client, mocker, keycloak_admin_mock, httpx_mock):
    url = re.compile(
        'http://keycloakadmin/realms//users/.*$',
    )
    httpx_mock.add_response(method='PUT', url=url, status_code=204)
    response = test_client.put(
        '/v1/admin/user',
        json={
            'last_login': True,
            'username': 'test_user',
            'announcement': {'project_code': 'test_project', 'announcement_pk': '111'},
        },
    )
    assert response.status_code == 200
    assert response.json().get('result')['announcement_test_project'] == '111'


def test_update_user_attribute_missing_username(test_client, mocker, keycloak_admin_mock):
    response = test_client.put(
        '/v1/admin/user',
        json={'last_login': True, 'announcement': {'project_code': 'test_project', 'announcement_pk': '111'}},
    )
    assert response.status_code == 422


def test_update_user_attribute_missing_updated_attrs(test_client, mocker, keycloak_admin_mock):
    response = test_client.put('/v1/admin/user', json={'username': 'test'})
    assert response.status_code == 400
    assert response.json().get('error_msg') == 'last_login or announcement is required'


def test_add_user_to_keycloak_new_group(test_client, mocker, keycloak_admin_mock):
    new_group = {'name': 'test_new_group', 'id': 'test_id'}
    user_id = 'test_user_id'

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_id', return_value=user_id)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_group_by_name', return_value=None)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.create_group')
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_group_by_name', return_value=new_group)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.add_user_to_group')

    response = test_client.post('/v1/admin/users/group', json={'username': 'test_user', 'groupname': 'test_group'})
    assert response.status_code == 200


def test_add_user_to_keycloak_existing_group(test_client, mocker, keycloak_admin_mock):
    existing_group = {'name': 'test_new_group', 'id': 'test_id'}
    user_id = 'test_user_id'

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_id', return_value=user_id)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_group_by_name', return_value=existing_group)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.add_user_to_group')

    response = test_client.post('/v1/admin/users/group', json={'username': 'test_user', 'groupname': 'test_group'})
    assert response.status_code == 200


def test_add_user_to_keycloak_group_missing_payload(test_client, keycloak_admin_mock):
    response = test_client.post(
        '/v1/admin/users/group',
        json={
            'username': 'test_user',
        },
    )
    assert response.status_code == 422


def test_remove_user_to_keycloak_existing_group(test_client, mocker, keycloak_admin_mock):
    existing_group = {'name': 'test_new_group', 'id': 'test_id'}
    user_id = 'test_user_id'

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_id', return_value=user_id)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_group_by_name', return_value=existing_group)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.remove_user_from_group')

    response = test_client.delete('/v1/admin/users/group', params={'username': 'test_user', 'groupname': 'test_group'})
    assert response.status_code == 200


def test_remove_user_to_keycloak_group_missing_params(test_client, keycloak_admin_mock):
    response = test_client.delete('/v1/admin/users/group', params={})
    assert response.status_code == 422


@pytest.mark.parametrize('get_users_in_role', [{'user_list_size': 20}], indirect=True)
@pytest.mark.parametrize('page_size', [5, 10])
def test_list_users_under_roles_pagination_1(test_client, mocker, keycloak_admin_mock, page_size, get_users_in_role):
    num_of_user = 20
    response = test_client.post(
        '/v1/admin/roles/users',
        json={
            'role_names': ['test-admin'],
            'page_size': page_size,
        },
    )
    assert response.status_code == 200
    assert response.json().get('num_of_pages') == num_of_user / page_size
    assert response.json().get('total') == num_of_user


def test_list_users_under_roles_filter_by_name(test_client, mocker, keycloak_admin_mock, get_users_in_role):
    response = test_client.post(
        '/v1/admin/roles/users',
        json={
            'role_names': ['test-admin'],
            'username': 'test_user_1',
        },
    )
    assert response.status_code == 200
    assert len(response.json().get('result')) == 1


def test_list_users_under_roles_filter_by_email(test_client, mocker, keycloak_admin_mock, get_users_in_role):
    response = test_client.post(
        '/v1/admin/roles/users',
        json={
            'role_names': ['test-admin'],
            'email': 'test_user_3@email.com',
        },
    )
    assert response.status_code == 200
    assert len(response.json().get('result')) == 1


def test_list_users_under_roles_filter_order_by_email(test_client, mocker, keycloak_admin_mock, get_users_in_role):
    response = test_client.post(
        '/v1/admin/roles/users', json={'role_names': ['test-admin'], 'order_by': 'email', 'order_type': 'desc'}
    )
    assert response.status_code == 200
    user_list = response.json().get('result')
    assert user_list[0].get('email') > user_list[1].get('email')


def test_list_users_under_roles_filter_order_by_username(test_client, mocker, keycloak_admin_mock, get_users_in_role):
    response = test_client.post(
        '/v1/admin/roles/users', json={'role_names': ['test-admin'], 'order_by': 'name', 'order_type': 'desc'}
    )
    assert response.status_code == 200
    user_list = response.json().get('result')
    assert user_list[0].get('name') > user_list[1].get('name')


@pytest.mark.parametrize('get_users_in_role', [{'user_list_size': 100}], indirect=True)
def test_list_user_stats_under_roles(test_client, mocker, keycloak_admin_mock, get_users_in_role, httpx_mock):
    num_of_user = 100
    response = test_client.get(
        '/v1/admin/roles/users/stats',
        params={'project_code': 'test_project'},
    )
    assert response.status_code == 200
    user_stats = response.json().get('result')
    assert user_stats['admin'] == num_of_user
    assert user_stats['collaborator'] == num_of_user
    assert user_stats['contributor'] == num_of_user


def test_list_user_stats_under_roles_with_invalid_project(test_client, mocker, keycloak_admin_mock):
    m = mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role')
    m.side_effect = Exception('Role invalid_project-admin is not found')

    response = test_client.get(
        '/v1/admin/roles/users/stats',
        params={'project_code': 'invalid_project'},
    )
    assert response.status_code == 500
    assert response.json().get('error_msg') == 'Role invalid_project-admin is not found'

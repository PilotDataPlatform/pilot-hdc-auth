# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

import pytest


@pytest.mark.parametrize('set_identity_backend', ['freeipa', 'openldap', 'keycloak'], indirect=True)
def test_user_add_ad_group(test_client, mocker, identity_client_mock, set_identity_backend):
    mocker.patch('app.services.data_providers.freeipa_client.FreeIPAClient.add_user_to_group')
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.add_user_to_group')
    response = test_client.put(
        '/v1/user/group',
        json={
            'user_email': 'test_email',
            'group_code': 'test_group',
            'operation_type': 'add',
        },
    )
    assert response.status_code == 200
    assert response.json().get('result') == 'add user test_email from ad group'


@pytest.mark.parametrize('set_identity_backend', ['freeipa', 'openldap', 'keycloak'], indirect=True)
def test_user_remove_ad_group(test_client, mocker, identity_client_mock, set_identity_backend):
    mocker.patch('app.services.data_providers.freeipa_client.FreeIPAClient.remove_user_from_group')
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.remove_user_from_group')

    response = test_client.put(
        '/v1/user/group',
        json={
            'user_email': 'test_email',
            'group_code': 'test_group',
            'operation_type': 'remove',
        },
    )
    assert response.status_code == 200
    assert response.json().get('result') == 'remove user test_email from ad group'


@pytest.mark.parametrize('set_identity_backend', ['freeipa', 'openldap', 'keycloak'], indirect=True)
def test_create_ad_group_200(test_client, mocker, identity_client_mock, set_identity_backend):
    response = test_client.post(
        '/v1/user/group',
        json={
            'group_name': 'test_group',
            'description': 'test description',
        },
    )
    assert response.status_code == 200


@pytest.mark.parametrize('set_identity_backend', ['freeipa', 'openldap', 'keycloak'], indirect=True)
def test_create_ad_group_exception_500(test_client, mocker, set_identity_backend):
    mocker.patch('app.services.data_providers.freeipa_client.FreeIPAClient.__init__', side_effect=Exception('Test'))
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.__init__', side_effect=Exception('Test'))
    mocker.patch('app.services.data_providers.keycloak_client.KeycloakClient.__init__', side_effect=Exception('Test'))
    response = test_client.post(
        '/v1/user/group',
        json={
            'group_name': 'test_group',
            'description': 'test description',
        },
    )
    assert response.status_code == 500


def test_create_ad_group_no_identity_backend(test_client):
    response = test_client.post(
        '/v1/user/group',
        json={
            'group_name': 'test_group',
            'description': 'test description',
        },
    )
    assert response.status_code == 500


@pytest.mark.parametrize('set_identity_backend', ['freeipa', 'openldap', 'keycloak'], indirect=True)
def test_delete_ad_group_200(test_client, identity_client_mock, set_identity_backend):
    response = test_client.request(
        'DELETE',
        '/v1/user/group',
        json={
            'group_name': 'test_group',
        },
    )
    assert response.status_code == 200


def test_delete_ad_group_no_identity_backend(test_client):
    response = test_client.request(
        'DELETE',
        '/v1/user/group',
        json={
            'group_name': 'test_group',
        },
    )
    assert response.status_code == 500


@pytest.mark.parametrize('set_identity_backend', ['freeipa', 'openldap', 'keycloak'], indirect=True)
def test_user_enable(test_client, mocker, keycloak_admin_mock, set_identity_backend):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_email',
        return_value={'id': uuid4(), 'username': 'fakeuser'},
    )
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.update_user_attributes', return_value='')

    response = test_client.put(
        '/v1/user/account',
        json={
            'user_email': 'test_email',
            'operation_type': 'enable',
        },
    )
    assert response.status_code == 200
    assert response.json().get('result') == 'enable user test_email'


@pytest.mark.parametrize('set_identity_backend', ['freeipa', 'openldap', 'keycloak'], indirect=True)
def test_user_disable(test_client, mocker, keycloak_admin_mock, identity_client_mock, set_identity_backend):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_email',
        return_value={'id': uuid4(), 'username': 'fakeuser'},
    )
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.update_user_attributes', return_value='')

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_realm_roles', return_value=[])
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.remove_user_realm_roles', return_value='')

    mocker.patch(
        'app.services.data_providers.freeipa_client.FreeIPAClient.get_user_by_email',
        return_value={'groups': ['fakegroup']},
    )
    mocker.patch(
        'app.services.data_providers.ldap_client.LdapClient.get_user_by_email', return_value={'groups': ['fakegroup']}
    )

    response = test_client.put(
        '/v1/user/account',
        json={
            'user_email': 'test_email',
            'operation_type': 'disable',
        },
    )
    assert response.status_code == 200
    assert response.json().get('result') == 'disable user test_email'


def test_user_disable_no_identity_backend(test_client, mocker, keycloak_admin_mock, identity_client_mock):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_email',
        return_value={'id': uuid4(), 'username': 'fakeuser'},
    )
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.update_user_attributes', return_value='')

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_realm_roles', return_value=[])
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.remove_user_realm_roles', return_value='')

    response = test_client.put(
        '/v1/user/account',
        json={
            'user_email': 'test_email',
            'operation_type': 'disable',
        },
    )
    assert response.status_code == 500

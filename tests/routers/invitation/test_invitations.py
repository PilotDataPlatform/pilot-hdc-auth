# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
import time
from uuid import UUID

import pytest
from common import ProjectClient
from common import ProjectNotFoundException

from app.config import ConfigSettings
from tests.conftest import FakeProjectObject

user_json = {
    'email': 'testuser@example.com',
    'enabled': True,
    'first_name': 'test',
    'id': '00000000-0000-0000-0000-49d95746c0a1',
    'last_name': 'user',
    'name': 'testuser',
    'role': 'member',
    'username': 'testuser',
    'attributes': {'status': ['active']},
}


def ops_admin_mock_client(mocker, user_exists, relation=True, role='fakeproject-admin'):
    class OperationsAdminMock:
        user_exists = ''
        role = ''
        relation = False

        async def get_user_by_email(self, anything):
            if self.user_exists:
                return user_json
            else:
                return None

        async def get_user_by_username(self, anything):
            return user_json

        async def get_user_realm_roles(self, anything):
            if self.relation:
                return [{'name': self.role}]
            else:
                return []

    ops_mock_client = OperationsAdminMock()
    ops_mock_client.user_exists = user_exists
    ops_mock_client.relation = relation
    ops_mock_client.role = role
    mocker.patch('app.components.identity.crud.IdentityCRUD.create_operations_admin', return_value=ops_mock_client)


@pytest.fixture
def ops_admin_mock(mocker):
    return ops_admin_mock_client(mocker, True)


@pytest.fixture
def ops_admin_mock_no_user(mocker):
    return ops_admin_mock_client(mocker, False)


@pytest.fixture
def ops_admin_mock_no_relation(mocker):
    return ops_admin_mock_client(mocker, True, relation=False)


@pytest.fixture
def ops_admin_mock_admin(mocker):
    return ops_admin_mock_client(mocker, True, role='platform-admin')


def identity_mock_client(monkeypatch, user_exists, is_in_ad=True):
    from app.services.data_providers.freeipa_client import FreeIPAClient

    class IdentityClientMock:
        user_data = ''
        user_exists = ''
        is_in_ad = True

        def __init__(self, *args, **kwargs):
            pass

        def fake_init(self):
            pass

        def connect(self):
            pass

        def user_exists(self, email):
            return self.is_in_ad

        def format_group_name(self, group_name):
            return group_name

        def get_user_by_email(self, email):
            return 'user_dn', self.user_data

        def add_user_to_group(self, user_dn, group_dn):
            return ''

    identity_mock_client = IdentityClientMock()
    identity_mock_client.user_data = {'username': 'testuser', 'email': 'testuser@example.com'}
    identity_mock_client.is_in_ad = is_in_ad
    monkeypatch.setattr(FreeIPAClient, '__init__', identity_mock_client.__init__)
    monkeypatch.setattr(FreeIPAClient, 'connect', identity_mock_client.connect)
    monkeypatch.setattr(FreeIPAClient, 'user_exists', identity_mock_client.user_exists)
    monkeypatch.setattr(FreeIPAClient, 'format_group_name', identity_mock_client.format_group_name)
    monkeypatch.setattr(FreeIPAClient, 'get_user_by_email', identity_mock_client.get_user_by_email)
    monkeypatch.setattr(FreeIPAClient, 'add_user_to_group', identity_mock_client.add_user_to_group)


@pytest.fixture
def identity_mock(monkeypatch):
    return identity_mock_client(monkeypatch, True)


@pytest.fixture
def identity_mock_not_in_ad(monkeypatch):
    return identity_mock_client(monkeypatch, True, is_in_ad=False)


@pytest.fixture
def identity_mock_no_user(monkeypatch):
    return identity_mock_client(monkeypatch, False)


@pytest.fixture
def patch_attachment(monkeypatch):
    monkeypatch.setattr(ConfigSettings, 'INVITE_ATTACHMENT', 'attachments/invite_attachment.pdf')


def test_create_invitation_exists_in_ad(
    test_client, httpx_mock, identity_client_mock, ops_admin_mock_no_user, mocker, keycloak_client_mock
):
    invited_by = 'admin'
    user = keycloak_client_mock.create_user(username=invited_by)
    project = FakeProjectObject()
    mocker.patch.object(ProjectClient, 'get', return_value=project)
    expected_request_payload = {
        'subject': f'Invitation to join the {project.name} project',
        'sender': 'test@example.com',
        'receiver': ['test1@example.com'],
        'msg_type': 'html',
        'attachments': [],
        'template': 'invitation/invite_project_register.html',
        'template_kwargs': {
            'inviter_email': user.email,
            'inviter_name': invited_by,
            'support_email': 'test@example.com',
            'support_url': '',
            'admin_email': 'test@example.com',
            'url': '',
            'login_url': '',
            'user_email': 'test1@example.com',
            'domain': '',
            'helpdesk_email': 'helpdesk@example.com',
            'platform_name': ConfigSettings.PROJECT_NAME,
            'register_url': '',
            'register_link': '',
            'project_name': 'Fake project',
            'project_code': 'fakeproject',
            'project_role': 'admin',
        },
    }
    httpx_mock.add_response(
        method='POST',
        url=f'{ConfigSettings.NOTIFY_SERVICE}email/',
        match_content=json.dumps(expected_request_payload).encode(),
        json={'result': 'success'},
        status_code=200,
    )
    payload = {
        'email': 'test1@example.com',
        'platform_role': 'member',
        'relationship': {
            'project_code': 'fakeproject',
            'project_role': 'admin',
            'inviter': 'admin',
        },
        'invited_by': invited_by,
        'inviter_project_role': 'admin',
    }
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200


def test_create_invitation_no_ad(
    test_client, httpx_mock, identity_client_mock, ops_admin_mock_no_user, mocker, keycloak_client_mock
):
    invited_by = 'admin'
    keycloak_client_mock.create_user(username=invited_by)
    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())

    httpx_mock.add_response(
        method='POST', url=ConfigSettings.NOTIFY_SERVICE + 'email/', json={'result': 'success'}, status_code=200
    )
    payload = {
        'email': 'test2@example.com',
        'platform_role': 'member',
        'relationship': {
            'project_code': 'fakeproject',
            'project_role': 'admin',
            'inviter': 'admin',
        },
        'invited_by': invited_by,
        'inviter_project_role': 'admin',
    }
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200


def test_create_invitation_exists_in_ad_contrib_403(
    test_client, httpx_mock, identity_client_mock, ops_admin_mock_no_user, mocker, keycloak_client_mock
):
    invited_by = 'admin'
    keycloak_client_mock.create_user(username=invited_by)
    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())

    payload = {
        'email': 'test5@example.com',
        'platform_role': 'member',
        'relationship': {
            'project_code': 'fakeproject',
            'project_role': 'admin',
            'inviter': 'admin',
        },
        'invited_by': invited_by,
        'inviter_project_role': 'contributor',
    }
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 403


def test_create_invitation_exists_in_ad_disable_external_403(
    test_client, httpx_mock, identity_client_mock, ops_admin_mock_no_user, mocker, monkeypatch, keycloak_client_mock
):
    invited_by = 'admin'
    keycloak_client_mock.create_user(username=invited_by)
    monkeypatch.setattr(ConfigSettings, 'ALLOW_EXTERNAL_REGISTRATION', False)
    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())

    payload = {
        'email': 'test5@example.com',
        'platform_role': 'member',
        'relationship': {
            'project_code': 'fakeproject',
            'project_role': 'admin',
            'inviter': 'admin',
        },
        'invited_by': invited_by,
        'inviter_project_role': 'contributor',
    }
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 403


def test_create_invitation_bad_inviter_project_role_400(
    test_client, httpx_mock, identity_client_mock, ops_admin_mock_no_user, mocker, monkeypatch, keycloak_client_mock
):
    invited_by = 'admin'
    keycloak_client_mock.create_user(username=invited_by)
    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())

    payload = {
        'email': 'test5@example.com',
        'platform_role': 'member',
        'relationship': {
            'project_code': 'fakeproject',
            'project_role': 'admin',
            'inviter': 'admin',
        },
        'invited_by': invited_by,
        'inviter_project_role': 'bad',
    }
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 400


def test_create_invitation_no_relation(
    test_client, httpx_mock, identity_mock_no_user, ops_admin_mock_no_user, mocker, keycloak_client_mock
):
    invited_by = 'admin'
    keycloak_client_mock.create_user(username=invited_by)
    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())
    httpx_mock.add_response(
        method='POST', url=ConfigSettings.NOTIFY_SERVICE + 'email/', json={'result': 'success'}, status_code=200
    )
    payload = {
        'email': 'test3@example.com',
        'platform_role': 'member',
        'invited_by': invited_by,
    }
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200


def test_create_invitation_admin(
    test_client, httpx_mock, identity_mock_no_user, ops_admin_mock_no_user, mocker, keycloak_client_mock
):
    invited_by = 'admin'
    user = keycloak_client_mock.create_user(username=invited_by)
    project = FakeProjectObject()
    mocker.patch.object(ProjectClient, 'get', return_value=project)
    expected_request_payload = {
        'subject': f'Invitation to join the {ConfigSettings.PROJECT_NAME}',
        'sender': 'test@example.com',
        'receiver': ['test4@example.com'],
        'msg_type': 'html',
        'attachments': [],
        'template': 'invitation/invite_without_project_register.html',
        'template_kwargs': {
            'inviter_email': user.email,
            'inviter_name': invited_by,
            'support_email': 'test@example.com',
            'support_url': '',
            'admin_email': 'test@example.com',
            'url': '',
            'login_url': '',
            'user_email': 'test4@example.com',
            'domain': '',
            'helpdesk_email': 'helpdesk@example.com',
            'platform_name': ConfigSettings.PROJECT_NAME,
            'register_url': '',
            'register_link': '',
            'platform_role': 'Platform Administrator',
        },
    }
    httpx_mock.add_response(
        method='POST',
        url=f'{ConfigSettings.NOTIFY_SERVICE}email/',
        match_content=json.dumps(expected_request_payload).encode(),
        json={'result': 'success'},
        status_code=200,
    )
    payload = {'email': 'test4@example.com', 'platform_role': 'admin', 'invited_by': invited_by}
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200


def test_create_invitation_admin_already_exists(test_client, httpx_mock, identity_mock, ops_admin_mock):
    payload = {'email': 'test4@example.com', 'platform_role': 'admin', 'invited_by': 'admin'}
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 400
    assert response.json()['result'] == '[ERROR] User already exists in platform'


def test_create_invitation_already_exists_in_project(test_client, httpx_mock, identity_mock, ops_admin_mock, mocker):
    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())
    payload = {
        'email': 'test2@example.com',
        'platform_role': 'member',
        'relationship': {
            'project_code': 'fakeproject',
            'project_role': 'admin',
            'inviter': 'admin',
        },
        'invited_by': 'admin',
        'inviter_project_role': 'admin',
    }
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 409
    assert response.json()['result'] == 'Invitation for this user already exists'


def test_create_invitation_not_in_ad(
    test_client,
    httpx_mock,
    identity_mock_not_in_ad,
    ops_admin_mock_no_user,
    patch_attachment,
    mocker,
    keycloak_client_mock,
):
    invited_by = 'admin'
    keycloak_client_mock.create_user(username=invited_by)
    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())

    httpx_mock.add_response(
        method='POST', url=ConfigSettings.NOTIFY_SERVICE + 'email/', json={'result': 'success'}, status_code=200
    )
    payload = {
        'email': 'test3@example.com',
        'platform_role': 'member',
        'relationship': {
            'project_code': 'fakeproject',
            'project_role': 'admin',
            'inviter': 'admin',
        },
        'invited_by': invited_by,
        'inviter_project_role': 'admin',
    }
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200


def test_get_invite_list(test_client, httpx_mock):
    payload = {
        'page': 0,
        'page_size': 1,
        'filters': {
            'project_code': 'fakeproject',
        },
    }
    response = test_client.post('/v1/invitation-list', json=payload)
    assert response.status_code == 200
    assert response.json()['result'][0]['project_code'] == 'fakeproject'


def test_get_invite_list_filter(test_client, httpx_mock):
    payload = {
        'page': 0,
        'page_size': 1,
        'filters': {
            'email': 'example.com',
        },
    }
    response = test_client.post('/v1/invitation-list', json=payload)
    assert response.status_code == 200
    assert response.json()['result'][0]['project_code'] == 'fakeproject'


def test_get_invite_list_order(test_client, httpx_mock, identity_mock, ops_admin_mock_no_user, keycloak_client_mock):
    invited_by = 'admin'
    keycloak_client_mock.create_user(username=invited_by)
    timestamp = time.time()
    httpx_mock.add_response(
        method='POST', url=ConfigSettings.NOTIFY_SERVICE + 'email/', json={'result': 'success'}, status_code=200
    )
    payload = {'email': f'a@ordertest_{timestamp}.com', 'platform_role': 'admin', 'invited_by': invited_by}
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200
    payload = {'email': f'b@ordertest_{timestamp}.com', 'platform_role': 'admin', 'invited_by': invited_by}
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200
    payload = {'email': f'c@ordertest_{timestamp}.com', 'platform_role': 'admin', 'invited_by': invited_by}
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200

    payload = {
        'page': 0,
        'page_size': 5,
        'order_by': 'email',
        'order_type': 'desc',
        'filters': {
            'email': f'ordertest_{timestamp}.com',
        },
    }
    response = test_client.post('/v1/invitation-list', json=payload)
    assert response.status_code == 200
    assert len(response.json()['result']) == 3
    assert response.json()['result'][0]['email'] == f'c@ordertest_{timestamp}.com'
    assert response.json()['result'][1]['email'] == f'b@ordertest_{timestamp}.com'
    assert response.json()['result'][2]['email'] == f'a@ordertest_{timestamp}.com'


def test_check_invite_email(test_client, httpx_mock, ops_admin_mock, mocker, keycloak_client_mock):
    keycloak_client_mock.create_role(user_id=UUID(user_json['id']), name='fakeproject-admin')
    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())
    payload = {
        'project_code': 'fakeproject',
    }
    response = test_client.get('/v1/invitation/check/testuser@example.com', params=payload)
    assert response.status_code == 200
    assert response.json()['result']['role'] == user_json['role']
    assert response.json()['result']['relationship']['project_code'] == 'fakeproject'


def test_check_invite_email_bad_project_id(test_client, httpx_mock, ops_admin_mock, mocker):
    mocker.patch.object(ProjectClient, 'get', side_effect=ProjectNotFoundException())

    payload = {
        'project_code': 'badcode',
    }
    response = test_client.get('/v1/invitation/check/testuser@example.com', params=payload)
    assert response.status_code == 404
    assert response.json()['error_msg'] == 'Project not found'


def test_check_invite_email_no_relation(test_client, httpx_mock, ops_admin_mock_no_relation, mocker):
    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())
    payload = {
        'project_code': 'fakeproject',
    }
    response = test_client.get('/v1/invitation/check/testuser@example.com', params=payload)
    assert response.status_code == 200
    assert response.json()['result']['role'] == user_json['role']
    assert response.json()['result']['relationship'] == {}


def test_check_invite_email_platform_admin(test_client, httpx_mock, ops_admin_mock_admin, mocker, keycloak_client_mock):
    keycloak_client_mock.create_role(user_id=UUID(user_json['id']), name='platform-admin')
    mocker.patch.object(ProjectClient, 'get', return_value=FakeProjectObject())
    payload = {
        'project_code': 'fakeproject',
    }
    response = test_client.get('/v1/invitation/check/testuser@example.com', params=payload)
    assert response.status_code == 200
    assert response.json()['result']['role'] == 'admin'
    assert response.json()['result']['relationship'] == {}


def test_check_invite_no_user(test_client, httpx_mock, ops_admin_mock_no_user):
    payload = {
        'project_code': 'fakeproject',
    }
    response = test_client.get('/v1/invitation/check/testuser@example.com', params=payload)
    assert response.status_code == 404
    assert response.json()['error_msg'] == 'User not found in keycloak'


def test_invite_create_for_update(test_client, httpx_mock, identity_mock, ops_admin_mock_no_user, keycloak_client_mock):
    invited_by = 'admin'
    keycloak_client_mock.create_user(username=invited_by)
    httpx_mock.add_response(
        method='POST', url=ConfigSettings.NOTIFY_SERVICE + 'email/', json={'result': 'success'}, status_code=200
    )
    payload = {'email': 'event@test.com', 'platform_role': 'admin', 'invited_by': invited_by}
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200


def test_invite_update(test_client, httpx_mock, ops_admin_mock):
    payload = {
        'page': 0,
        'page_size': 5,
        'order_by': 'email',
        'order_type': 'desc',
        'filters': {
            'email': 'event@test.com',
        },
    }
    response = test_client.post('/v1/invitation-list', json=payload)
    assert response.status_code == 200
    invite_id = response.json()['result'][0]['id']

    payload = {
        'status': 'complete',
    }
    response = test_client.put(f'/v1/invitation/{invite_id}', json=payload)
    assert response.status_code == 200

    payload = {
        'invitation_id': invite_id,
    }
    response = test_client.get('/v1/events', params=payload)
    assert response.status_code == 200
    assert response.json()['result'][0]['target_user'] == user_json['username']
    assert response.json()['result'][0]['target_user_id'] == str(user_json['id'])

# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

user_json = {
    'email': 'testuser@example.com',
    'enabled': True,
    'first_name': 'test',
    'id': '00000000-0000-0000-0000-806cd88448f6',
    'last_name': 'user',
    'name': 'testuser',
    'role': 'member',
    'username': 'testuser',
    'attributes': {'status': ['active']},
}


def test_create_event(test_client, keycloak_admin_mock, keycloak_client_mock):
    operator = 'admin'
    keycloak_client_mock.create_user(username=operator)
    keycloak_client_mock.create_user(id_=UUID(user_json['id']), username=user_json['username'])
    payload = {
        'target_user': 'testuser',
        'operator': operator,
        'event_type': 'ACCOUNT_ACTIVATED',
        'detail': {},
    }
    response = test_client.post('/v1/events', json=payload)
    assert response.status_code == 200


def test_create_event_role(test_client, keycloak_admin_mock, keycloak_client_mock):
    operator = 'admin'
    keycloak_client_mock.create_user(username=operator)
    keycloak_client_mock.create_user(id_=UUID(user_json['id']), username=user_json['username'])
    payload = {
        'target_user': 'testuser',
        'operator': operator,
        'event_type': 'ROLE_CHANGE',
        'detail': {
            'project_code': 'fakecode',
            'to': 'admin',
            'from': 'contributor',
        },
    }
    response = test_client.post('/v1/events', json=payload)
    assert response.status_code == 200


def test_create_event_invite(test_client, keycloak_admin_mock, keycloak_client_mock):
    operator = 'admin'
    keycloak_client_mock.create_user(username=operator)
    keycloak_client_mock.create_user(username=user_json['username'])
    payload = {
        'operator': operator,
        'event_type': 'INVITE_TO_PROJECT',
        'detail': {
            'project_code': 'fakecode',
            'project_role': 'admin',
        },
    }
    response = test_client.post('/v1/events', json=payload)
    assert response.status_code == 200


def test_create_event_role_no_operator(test_client, keycloak_admin_mock, keycloak_client_mock):
    target_user = 'testuser'
    keycloak_client_mock.create_user(username=target_user)
    keycloak_client_mock.create_user(username=user_json['username'])
    payload = {
        'target_user': target_user,
        'operator': '',
        'event_type': 'ACCOUNT_ACTIVATED',
        'detail': {},
    }
    response = test_client.post('/v1/events', json=payload)
    assert response.status_code == 200


def test_list_events_query_200(test_client):
    payload = {
        'project_code': 'fakecode',
    }
    response = test_client.get('/v1/events', params=payload)
    assert response.status_code == 200
    for event in response.json()['result']:
        if not event['event_type'] in ['ACCOUNT_ACTIVATED', 'ACCOUNT_DISABLE']:
            assert event['detail']['project_code'] == 'fakecode'


def test_list_events_query_user_200(test_client):
    payload = {
        'user_id': user_json['id'],
    }
    response = test_client.get('/v1/events', params=payload)
    assert response.status_code == 200
    assert response.json()['result'][0]['target_user'] == user_json['username']

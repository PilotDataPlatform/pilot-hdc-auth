# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.


def test_find_hbac_rule(test_client, identity_client_mock):
    response = test_client.get(
        '/v1/vm/hbac',
        params={
            'name': 'randomtest',
        },
    )
    assert response.status_code == 200
    assert response.json()['name'] == 'access_ldap-randomtest.dev.hdc.test.eu'


def test_find_hbac_rule_not_found(test_client, identity_client_mock):
    response = test_client.get(
        '/v1/vm/hbac',
        params={
            'name': 'notrandomtest',
        },
    )
    assert response.status_code == 404


def test_add_user_to_hbac(test_client, identity_client_mock, mocker):
    mocker.patch(
        'app.services.data_providers.freeipa_client.FreeIPAClient.get_user_by_username',
        return_value={
            'username': 'testuser3',
            'email': 'test@test.test',
            'first_name': 'test',
            'last_name': 'test',
            'groups': [],
            'hbac_rules': [],
        },
    )
    response = test_client.post(
        '/v1/vm/hbac/add',
        params={
            'rule': 'randomtest',
            'username': 'testuser3',
        },
    )

    assert response.status_code == 200


def test_remove_user_from_hbac(test_client, identity_client_mock, mocker):
    mocker.patch(
        'app.services.data_providers.freeipa_client.FreeIPAClient.get_user_by_username',
        return_value={
            'username': 'testuser3',
            'email': 'test@test.test',
            'first_name': 'test',
            'last_name': 'test',
            'groups': [],
            'hbac_rules': [],
        },
    )
    response = test_client.delete(
        '/v1/vm/hbac/remove',
        params={
            'rule': 'randomtest',
            'username': 'testuser3',
        },
    )

    assert response.status_code == 200

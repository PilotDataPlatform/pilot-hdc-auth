# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from http import HTTPStatus
from urllib.parse import urlencode
from uuid import UUID

import pytest

from app.components.exceptions import NotFound


class TestKeycloakClient:
    def test_headers_property_returns_dict_with_authorization_header(self, keycloak_client, fake):
        keycloak_client.access_token = fake.pystr()
        headers = {
            'Authorization': f'Bearer {keycloak_client.access_token}',
        }
        assert keycloak_client.headers == headers

    @pytest.mark.parametrize(
        'current_time,token_expiration,expected_result',
        [
            (10.0, 0, True),
            (90.0, 100, True),
            (91.0, 100, True),
            (89.0, 100, False),
        ],
    )
    def test_is_authorization_expiring_soon_returns_expected_result_considering_10_seconds_margin(
        self, current_time, token_expiration, expected_result, keycloak_client, mocker
    ):
        mocker.patch('time.monotonic', return_value=current_time)
        keycloak_client.access_token_expiration = token_expiration

        assert keycloak_client.is_authorization_expiring_soon is expected_result

    async def test_request_makes_request_and_returns_response(self, keycloak_client, httpserver, fake):
        expected_response_json = {'key': fake.pystr()}
        httpserver.expect_oneshot_request('/path', method='GET').respond_with_json(expected_response_json)

        response = await keycloak_client._request('GET', '/path')

        assert response.json() == expected_response_json

    async def test_request_performs_authorization_and_request_retry_when_server_responds_with_unauthorized_status_code(
        self, keycloak_client, httpserver, fake
    ):
        token_url = f'/realms/{keycloak_client.realm}/protocol/openid-connect/token'
        expected_response_json = {'key': fake.pystr()}
        httpserver.expect_ordered_request('/path', method='GET').respond_with_json({}, status=HTTPStatus.UNAUTHORIZED)
        httpserver.expect_ordered_request(token_url, method='POST').respond_with_json(
            {'access_token': 'token', 'expires_in': 1}
        )
        httpserver.expect_ordered_request('/path', method='GET').respond_with_json(expected_response_json)

        response = await keycloak_client._request('GET', '/path')

        assert response.json() == expected_response_json

    async def test_request_performs_request_with_client_headers_and_retry_request_with_fresh_token_in_headers(
        self, keycloak_client, httpserver, fake
    ):
        def compare_header_values(header_name: str, actual: str, expected: str) -> bool:
            return actual == expected

        token_url = f'/realms/{keycloak_client.realm}/protocol/openid-connect/token'
        fresh_token = fake.pystr()
        httpserver.expect_ordered_request(
            '/path', method='GET', headers=keycloak_client.headers, header_value_matcher=compare_header_values
        ).respond_with_json({}, status=HTTPStatus.UNAUTHORIZED)
        httpserver.expect_ordered_request(token_url, method='POST').respond_with_json(
            {'access_token': fresh_token, 'expires_in': 1}
        )
        expected_request_headers = {'Authorization': f'Bearer {fresh_token}'}
        httpserver.expect_ordered_request(
            '/path', method='GET', headers=expected_request_headers, header_value_matcher=compare_header_values
        ).respond_with_json({})

        response = await keycloak_client._request('GET', '/path')

        assert response.status_code == 200

    async def test_request_raises_not_found_exception_when_server_responds_with_not_found_status_code_on_first_request(
        self, keycloak_client, httpserver
    ):
        httpserver.expect_oneshot_request('/path', method='GET').respond_with_json({}, status=HTTPStatus.NOT_FOUND)

        with pytest.raises(NotFound):
            await keycloak_client._request('GET', '/path')

    async def test_request_raises_not_found_exception_when_server_responds_with_not_found_status_code_on_second_request(
        self, keycloak_client, httpserver
    ):
        token_url = f'/realms/{keycloak_client.realm}/protocol/openid-connect/token'
        httpserver.expect_ordered_request('/path', method='GET').respond_with_json({}, status=HTTPStatus.UNAUTHORIZED)
        httpserver.expect_ordered_request(token_url, method='POST').respond_with_json(
            {'access_token': 'token', 'expires_in': 1}
        )
        httpserver.expect_ordered_request('/path', method='GET').respond_with_json({}, status=HTTPStatus.NOT_FOUND)

        with pytest.raises(NotFound):
            await keycloak_client._request('GET', '/path')

    async def test_authorize_makes_request_to_obtain_token_and_stores_it_together_with_expiration_time(
        self, keycloak_client, httpserver, fake, mocker
    ):
        token_url = f'/realms/{keycloak_client.realm}/protocol/openid-connect/token'
        current_time = fake.pyint()
        mocker.patch('time.monotonic', return_value=current_time)
        expected_request_data = urlencode(
            {
                'scope': 'openid',
                'grant_type': keycloak_client.grant_type,
                'client_id': keycloak_client.client_id,
                'client_secret': keycloak_client.client_secret,
            },
            doseq=True,
        )
        expected_access_token = fake.pystr()
        access_token_expiration = fake.pyint()
        expected_access_token_expiration = current_time + access_token_expiration
        httpserver.expect_request(token_url, method='POST', data=expected_request_data).respond_with_json(
            {'access_token': expected_access_token, 'expires_in': access_token_expiration}
        )

        await keycloak_client.authorize()

        assert keycloak_client.access_token == expected_access_token
        assert keycloak_client.access_token_expiration == expected_access_token_expiration

    async def test_get_user_returns_user_by_id(self, keycloak_client, httpserver, fake):
        user_id = fake.uuid4()
        user_url = f'/admin/realms/{keycloak_client.realm}/users/{user_id}'
        expected_user = {'id': user_id}
        httpserver.expect_request(user_url, method='GET').respond_with_json(expected_user)

        received_user = await keycloak_client.get_user(UUID(user_id))

        assert received_user == expected_user

    async def test_get_user_by_username_returns_first_user_by_exact_match_of_username(
        self, keycloak_client, httpserver, fake
    ):
        users_url = f'/admin/realms/{keycloak_client.realm}/users'
        username = fake.user_name()
        expected_request_params = {'username': username, 'exact': 'true'}
        expected_user = {'username': username}
        httpserver.expect_request(users_url, method='GET', query_string=expected_request_params).respond_with_json(
            [expected_user]
        )

        received_user = await keycloak_client.get_user_by_username(username)

        assert received_user == expected_user

    async def test_get_user_by_username_raises_not_found_exception_when_there_is_no_match(
        self, keycloak_client, httpserver, fake
    ):
        users_url = f'/admin/realms/{keycloak_client.realm}/users'
        httpserver.expect_request(users_url, method='GET').respond_with_json([])

        with pytest.raises(NotFound):
            await keycloak_client.get_user_by_username('non-existing')

    async def test_get_user_roles_returns_list_of_user_roles(self, keycloak_client, httpserver, fake):
        user_id = fake.uuid4()
        user_url = f'/admin/realms/{keycloak_client.realm}/users/{user_id}/role-mappings/realm'
        expected_roles = [{'id': fake.uuid4()}]
        httpserver.expect_request(user_url, method='GET').respond_with_json(expected_roles)

        received_roles = await keycloak_client.get_user_roles(UUID(user_id))

        assert expected_roles == received_roles

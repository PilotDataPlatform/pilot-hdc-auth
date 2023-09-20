# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from alembic.command import upgrade
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_sqlalchemy import DBSessionMiddleware
from fastapi_sqlalchemy import db as db_session
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema
from sqlalchemy_utils import create_database
from sqlalchemy_utils import database_exists
from starlette.config import environ
from testcontainers.postgres import PostgresContainer

environ['NOTIFY_SERVICE'] = 'http://notify'
environ['PROJECT_SERVICE'] = 'http://project'
environ['WORKSPACE_SERVICE'] = 'http://workspace'

environ['EMAIL_SUPPORT'] = 'test@example.com'
environ['EMAIL_ADMIN'] = 'test@example.com'
environ['EMAIL_HELPDESK'] = 'helpdesk@example.com'

environ['IDENTITY_BACKEND'] = ''

environ['LDAP_URL'] = 'http://ldap_host'
environ['LDAP_ADMIN_DN'] = ''
environ['LDAP_ADMIN_SECRET'] = ''
environ['LDAP_OU'] = ''
environ['LDAP_DC1'] = ''
environ['LDAP_DC2'] = ''
environ['LDAP_GROUP_OBJECTCLASS'] = ''
environ['LDAP_USER_GROUP'] = 'testgroup'
environ['LDAP_PREFIX'] = 'testprefix'
environ['LDAP_USER_OBJECTCLASS'] = ''
environ['LDAP_USER_QUERY_FIELD'] = ''
environ['LDAP_SET_GIDNUMBER'] = 'false'
environ['LDAP_GID_LOWER_BOUND'] = '10'
environ['LDAP_GID_UPPER_BOUND'] = '100'
environ['LDAP_OPT_REFERRALS'] = '0'

environ['RDS_HOST'] = 'db'
environ['RDS_PORT'] = '5432'
environ['RDS_DBNAME'] = 'test'
environ['RDS_USER'] = 'test'
environ['RDS_PWD'] = 'test'
environ['RDS_SCHEMA_PREFIX'] = 'pilot'

environ['KEYCLOAK_ID'] = ''
environ['KEYCLOAK_SERVER_URL'] = 'http://keycloak'
environ['KEYCLOAK_CLIENT_ID'] = ''
environ['KEYCLOAK_SECRET'] = ''
environ['KEYCLOAK_REALM'] = ''

environ['DOMAIN_NAME'] = ''
environ['START_PATH'] = 'test-start-path'
environ['GUIDE_PATH'] = 'test-guide-path'

environ['AD_USER_GROUP'] = ''
environ['AD_ADMIN_GROUP'] = ''
environ['PROJECT_NAME'] = 'Pilot'
environ['INVITATION_URL_LOGIN'] = ''
environ['INVITATION_REGISTER_URL'] = ''

environ['REDIS_HOST'] = 'redis://redis'
environ['REDIS_PASSWORD'] = 'redis'

PROJECT_DATA = {
    'id': str(uuid4()),
    'name': 'Fake project',
    'code': 'fakeproject',
}

TEST_USER = {
    'username': 'test_user',
    'email': 'test_user@test.com',
    'id': '00000000-0000-0000-0000-0624d6078073',
    'firstName': 'firstName',
    'lastName': 'lastName',
    'attributes': {'status': ['active']},
}


class FakeProjectObject:
    id = PROJECT_DATA['id']
    code = PROJECT_DATA['code']
    name = PROJECT_DATA['name']

    async def json(self):
        return PROJECT_DATA


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


@pytest.fixture
def get_users_in_role(httpx_mock, request):
    user_list_size = None

    if hasattr(request, 'param'):
        user_list_size = request.param.get('user_list_size')
    if not user_list_size:
        user_list_size = 10
    url = re.compile('^http://keycloakadmin/realms//roles/.*/users$')
    httpx_mock.add_response(method='GET', url=url, json=create_test_user_list(size=user_list_size))


@pytest.fixture
def get_user_realm_mock(httpx_mock, request):
    realm_roles = None

    if hasattr(request, 'param'):
        realm_roles = request.param.get('realm_roles')

    if not realm_roles:
        realm_roles = [
            {
                'id': '2e3897e0-e6f5-48a0-92ab-0128d7f45bd5',
                'name': 'indoctestproject-collaborator',
            }
        ]

    url = re.compile(
        '^http://keycloakadmin/realms//users/.*/role-mappings/realm$',
    )
    httpx_mock.add_response(method='GET', url=url, json=realm_roles)


@pytest.fixture
def keycloak_admin_mock(mocker, httpx_mock, request):  # noqa: C901
    test_user = None

    if hasattr(request, 'param'):
        test_user = request.param.get('test_user')
    if not test_user:
        test_user = TEST_USER

    class KeycloakAdminMock:
        token = {'access_token': 'testing', 'refresh_token': 'testing'}

        async def connect(*args, **kwargs):
            pass

        async def get_user_id(self, *args, **kwargs):
            return test_user['id']

        async def get_users(self, *args, **kwargs):
            return [test_user]

        async def get_user(self, *args, **kwargs):
            return test_user

        async def get_realm_roles(*args, **kwargs):
            return [{'name': 'indoctestproject-admin'}, {'name': 'indoctestproject-collaborator'}]

        async def assign_realm_roles(*args, **kwargs):
            pass

        async def update_user(*args, **kwargs):
            pass

    mocker.patch('app.components.identity.crud.KeycloakAdmin', return_value=KeycloakAdminMock)

    class OperationsUserMock:
        async def get_token(self, *args, **kwargs):
            return {'access_token': 'test', 'refresh_token': 'test'}

        async def get_refresh_token(self, *args, **kwargs):
            return {'access_token': 'test', 'refresh_token': 'test'}

    mocker.patch('app.resources.keycloak_api.ops_user.OperationsUser.create', return_value=OperationsUserMock())


@pytest.fixture(scope='function')
def set_identity_backend(request, monkeypatch):
    from app.config import ConfigSettings

    monkeypatch.setenv('IDENTITY_BACKEND', request.param)
    monkeypatch.setattr(ConfigSettings, 'IDENTITY_BACKEND', request.param)
    yield request.param


@pytest.fixture
async def identity_client_mock(mocker):  # noqa: C901
    class Conn:
        async def add_s(self, *args, **kwargs):
            pass

        async def unbind_s(self, *args, **kwargs):
            pass

        async def delete(self, *args, **kwargs):
            pass

        async def delete_s(self, *args, **kwargs):
            pass

    class Client:
        async def group_add(self, *args, **kwargs):
            pass

        async def group_del(self, *args, **kwargs):
            pass

        async def user_del(self, *args, **kwargs):
            pass

        async def user_find(self, *args, **kwargs):
            return {
                'username': 'test',
                'email': 'test@test.com',
                'groups': ['testgroup'],
            }

        async def get_users(self, *args, **kwargs):
            return [
                {
                    'username': 'test',
                    'email': 'test@test.com',
                    'groups': ['testgroup'],
                }
            ]

        async def get_groups(self, *args, **kwargs):
            return [
                {
                    'name': 'test',
                    'id': 'test',
                    'subgroups': ['testgroup'],
                }
            ]

        async def get_group_by_path(self, *args, **kwargs):
            return {
                'name': 'test',
                'id': 'test',
                'subGroups': ['testgroup'],
            }

        async def group_user_add(self, *args, **kwargs):
            pass

        async def group_user_remove(self, *args, **kwargs):
            pass

        async def create_group(self, *args, **kwargs):
            return {
                'name': 'test',
                'id': 'test',
                'subgroups': ['testgroup'],
            }

        async def delete_group(self, *args, **kwargs):
            pass

        async def create_user(self, *args, **kwargs):
            return {
                'username': 'test',
                'email': 'test@test.com',
                'groups': ['testgroup'],
            }

        async def user_add(self, *args, **kwargs):
            return {
                'result': {
                    'uid': 'test',
                    'mail': 'test@test.com',
                    'givenname': 'Test',
                    'sn': 'Test',
                }
            }

        async def change_password(self, *args, **kwargs):
            pass

    class IdentityClientMock:
        def __init__(self, *args, **kwargs):
            self.objectclass = ['group'.encode('utf-8')]
            self.conn = Conn()
            self.group_dn_template = 'cn={cn},ou={ou},dc={dc1},dc={dc2}'
            self.dc_template = ''
            self.client = Client()

        async def connect(self, *args, **kwargs):
            pass

        def disconnect(self, *args, **kwargs):
            pass

        def format_group_dn(self, group_name):
            return group_name

    mocker.patch('app.services.data_providers.freeipa_client.FreeIPAClient.__init__', IdentityClientMock.__init__)
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.__init__', IdentityClientMock.__init__)
    mocker.patch('app.services.data_providers.keycloak_client.KeycloakClient.__init__', IdentityClientMock.__init__)
    mocker.patch('app.services.data_providers.freeipa_client.FreeIPAClient.connect', IdentityClientMock.connect)
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.connect', IdentityClientMock.connect)
    mocker.patch('app.services.data_providers.keycloak_client.KeycloakClient.connect', IdentityClientMock.connect)


@pytest.fixture()
def keycloak_create_role_mock(mocker, httpx_mock):
    KeycloakMock = AsyncMock()
    KeycloakMock.token = {'access_token': 'testing', 'refresh_token': 'testing'}
    mocker.patch('app.components.identity.crud.KeycloakAdmin', return_value=KeycloakMock)
    from app.config import ConfigSettings

    httpx_mock.add_response(
        url=f'{ConfigSettings.KEYCLOAK_SERVER_URL}admin/realms/{ConfigSettings.KEYCLOAK_REALM}/roles',
        method='POST',
        status_code=201,
        json={},
    )


@pytest.fixture()
async def list_roles(test_async_client):
    payload = {
        'project_code': 'test_project',
    }
    response = await test_async_client.get('/v1/permissions/metadata', params=payload)
    assert response.status_code == 200
    permission = response.json()['result'][0]
    permission_id = permission['id']
    permission_id_2 = response.json()['result'][1]['id']
    return permission_id, permission_id_2


@pytest.fixture()
async def create_rules(test_async_client, list_roles):
    permission_id, permission_id_2 = list_roles
    payload = {
        'project_code': 'test_project',
        'rules': {
            'testrole': [permission_id, permission_id_2],
        },
    }
    response = await test_async_client.post('/v1/permissions/bulk/create', json=payload)
    assert response.status_code == 200


@pytest.fixture()
def db_for_common_tests(test_client, db):
    db_url = db.get_connection_url()
    DBSessionMiddleware(app=test_client.app, db_url=db_url)
    with db_session():
        yield db_url


@pytest.fixture(scope='session', autouse=True)
def db():
    from app.config import ConfigSettings

    with PostgresContainer('postgres:14.1') as postgres:
        postgres_uri = postgres.get_connection_url()
        if not database_exists(postgres_uri):
            create_database(postgres_uri)
        engine = create_engine(postgres_uri)

        if not engine.dialect.has_schema(engine, ConfigSettings.RDS_SCHEMA_PREFIX + '_invitation'):
            engine.execute(CreateSchema(ConfigSettings.RDS_SCHEMA_PREFIX + '_invitation'))

        if not engine.dialect.has_schema(engine, ConfigSettings.RDS_SCHEMA_PREFIX + '_event'):
            engine.execute(CreateSchema(ConfigSettings.RDS_SCHEMA_PREFIX + '_event'))

        if not engine.dialect.has_schema(engine, ConfigSettings.RDS_SCHEMA_PREFIX + '_ldap'):
            engine.execute(CreateSchema(ConfigSettings.RDS_SCHEMA_PREFIX + '_ldap'))

        if not engine.dialect.has_schema(engine, ConfigSettings.RDS_SCHEMA_PREFIX + '_casbin'):
            engine.execute(CreateSchema(ConfigSettings.RDS_SCHEMA_PREFIX + '_casbin'))
        yield postgres


@pytest.fixture(scope='session')
def settings(db):
    from app.config import ConfigSettings

    ConfigSettings.RDS_DB_URI = db.get_connection_url()
    yield ConfigSettings


@pytest.fixture
def app(settings, identity_crud) -> FastAPI:
    from app import create_app
    from app.components.identity.dependencies import get_identity_crud
    from app.config import get_settings

    config = Config()
    config.set_main_option('script_location', 'migrations')
    config.set_main_option('sqlalchemy.url', settings.RDS_DB_URI)
    upgrade(config, 'head')

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_identity_crud] = lambda: identity_crud
    yield app


@pytest.fixture
def test_client(app):
    client = TestClient(app)
    return client


@pytest.fixture
def test_async_client(app):
    client = AsyncClient(app=app, base_url='http://test')
    return client


@pytest.fixture
def non_mocked_hosts() -> list:
    return ['test', '127.0.0.1']


pytest_plugins = [
    'tests.fixtures.components.identity',
    'tests.fixtures.components.keycloak',
    'tests.fixtures.casbin',
    'tests.fixtures.db',
    'tests.fixtures.fake',
]

# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import logging
from functools import lru_cache
from typing import Any

from pydantic import BaseSettings
from pydantic import Extra


class Settings(BaseSettings):
    """Store service configuration settings."""

    APP_NAME: str = 'service_auth'
    VERSION: str = '2.2.30'
    PORT: int = 5061
    HOST: str = '0.0.0.0'
    WORKERS: int = 1

    LOGGING_LEVEL: int = logging.INFO
    LOGGING_FORMAT: str = 'json'

    NOTIFY_SERVICE: str = 'http://notification.utility:5065'
    PROJECT_SERVICE: str = 'http://project.utility:5064'
    WORKSPACE_SERVICE: str = 'http://workspace.utility:5068'

    SERVICE_CLIENT_TIMEOUT: int = 5

    EMAIL_SUPPORT: str
    EMAIL_ADMIN: str
    EMAIL_HELPDESK: str

    IDENTITY_BACKEND: str
    FREEIPA_URL: str | None
    FREEIPA_USERNAME: str | None
    FREEIPA_PASSWORD: str | None
    USER_OBJECT_GROUPS: str = ''

    # LDAP configs
    LDAP_URL: str | None
    LDAP_ADMIN_DN: str | None
    LDAP_ADMIN_SECRET: str | None
    LDAP_OU: str | None
    LDAP_DC1: str | None
    LDAP_DC2: str | None
    LDAP_USER_GROUP: str | None
    LDAP_USER_QUERY_FIELD: str | None
    LDAP_PREFIX: str = 'hdc'
    LDAP_SET_GIDNUMBER: bool | None
    LDAP_OPT_REFERRALS: int | None
    LDAP_GID_LOWER_BOUND: int | None
    LDAP_GID_UPPER_BOUND: int | None
    LDAP_GROUP_OBJECTCLASS: str | None

    # BFF RDS
    RDS_HOST: str
    RDS_PORT: str
    RDS_DBNAME: str
    RDS_USER: str
    RDS_PWD: str
    RDS_SCHEMA_PREFIX: str
    RDS_PRE_PING: bool = False

    # Keycloak config
    KEYCLOAK_ID: str
    KEYCLOAK_SERVER_URL: str
    KEYCLOAK_CLIENT_ID: str
    KEYCLOAK_SECRET: str
    KEYCLOAK_REALM: str

    DOMAIN_NAME: str
    START_PATH: str
    GUIDE_PATH: str

    TEST_PROJECT_CODE: str = 'test-project-code'
    TEST_PROJECT_ROLE: str = 'collaborator'
    TEST_PROJECT_NAME: str = 'Indoc Test Project'

    OPEN_TELEMETRY_ENABLED: bool = False
    OPEN_TELEMETRY_HOST: str = '127.0.0.1'
    OPEN_TELEMETRY_PORT: int = 6831

    ENABLE_ACTIVE_DIRECTORY: bool = False
    AD_USER_GROUP: str
    AD_ADMIN_GROUP: str
    PROJECT_NAME: str

    INVITE_ATTACHMENT: str = ''
    INVITE_ATTACHMENT_NAME: str = ''
    INVITATION_URL_LOGIN: str
    INVITE_EXPIRY_MINUTES: int = 120
    INVITATION_REGISTER_URL: str
    ALLOW_EXTERNAL_REGISTRATION: bool = True
    EMAIL_PROJECT_REGISTER_URL: str = ''
    EMAIL_PROJECT_SUPPORT_URL: str = ''

    REDIS_HOST: str = '127.0.0.1'
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str

    ROLE_NAME_REGEX: str = '^[a-zA-Z0-9_]*$'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = Extra.allow

    def __init__(self, *args: Any, **kwds: Any) -> None:
        super().__init__(*args, **kwds)
        self.NOTIFY_SERVICE += '/v1/'
        self.WORKSPACE_SERVICE += '/v1/'
        self.REDIS_URL = f'redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}'
        self.RDS_DB_URI = (
            f'postgresql://{self.RDS_USER}:{self.RDS_PWD}@{self.RDS_HOST}:{self.RDS_PORT}/{self.RDS_DBNAME}'
        )
        self.LDAP_USER_OBJECT_GROUPS = self.USER_OBJECT_GROUPS.split(',')


@lru_cache(1)
def get_settings():
    settings = Settings()
    return settings


ConfigSettings = get_settings()

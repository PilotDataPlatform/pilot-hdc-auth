# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import LoggerFactory

from app.config import ConfigSettings
from app.services.data_providers.freeipa_client import FreeIPAClient
from app.services.data_providers.keycloak_client import KeycloakClient
from app.services.data_providers.ldap_client import LdapClient

_logger = LoggerFactory(
    __name__,
    level_default=ConfigSettings.LOG_LEVEL_DEFAULT,
    level_file=ConfigSettings.LOG_LEVEL_FILE,
    level_stdout=ConfigSettings.LOG_LEVEL_STDOUT,
    level_stderr=ConfigSettings.LOG_LEVEL_STDERR,
).get_logger()


def get_identity_client():
    if ConfigSettings.IDENTITY_BACKEND == 'freeipa':
        return FreeIPAClient

    elif ConfigSettings.IDENTITY_BACKEND == 'openldap':
        return LdapClient

    elif ConfigSettings.IDENTITY_BACKEND == 'keycloak':
        return KeycloakClient

    else:
        msg = 'Backend identity is not configured'
        _logger.error(msg)
        raise Exception(msg)

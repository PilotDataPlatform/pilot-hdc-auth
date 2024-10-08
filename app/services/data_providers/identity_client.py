# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from app.config import ConfigSettings
from app.logger import logger
from app.services.data_providers.freeipa_client import FreeIPAClient
from app.services.data_providers.keycloak_client import KeycloakClient
from app.services.data_providers.ldap_client import LdapClient


def get_identity_client():
    if ConfigSettings.IDENTITY_BACKEND == 'freeipa':
        return FreeIPAClient

    elif ConfigSettings.IDENTITY_BACKEND == 'openldap':
        return LdapClient

    elif ConfigSettings.IDENTITY_BACKEND == 'keycloak':
        return KeycloakClient

    else:
        msg = 'Backend identity is not configured'
        logger.error(msg)
        raise Exception(msg)

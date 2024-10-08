# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi_sqlalchemy import db

from app.logger import logger
from app.models.api_response import EAPIResponseCode
from app.models.sql_ldap_id import LdapIdModel
from app.resources.error_handler import APIException


def create_ldap_id(group_name: str) -> LdapIdModel:
    try:
        ldap_id = LdapIdModel(group_name=group_name)
        db.session.add(ldap_id)
        db.session.commit()
        return ldap_id
    except Exception as e:
        error_msg = f'Error creating ldap id in psql: {str(e)}'
        logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

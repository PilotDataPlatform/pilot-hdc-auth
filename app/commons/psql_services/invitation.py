# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import LoggerFactory
from fastapi_sqlalchemy import db

from app.config import ConfigSettings
from app.models.api_response import EAPIResponseCode
from app.models.sql_invitation import InvitationModel
from app.resources.error_handler import APIException

_logger = LoggerFactory(
    'api_invitation',
    level_default=ConfigSettings.LOG_LEVEL_DEFAULT,
    level_file=ConfigSettings.LOG_LEVEL_FILE,
    level_stdout=ConfigSettings.LOG_LEVEL_STDOUT,
    level_stderr=ConfigSettings.LOG_LEVEL_STDERR,
).get_logger()


def query_invites(query: dict) -> list:
    try:
        invites = db.session.query(InvitationModel).filter_by(**query).all()
    except Exception as e:
        error_msg = f'Error querying invite in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
    return invites


def create_invite(model_data: dict) -> InvitationModel:
    try:
        invitation_entry = InvitationModel(**model_data)
        db.session.add(invitation_entry)
        db.session.commit()
        return invitation_entry
    except Exception as e:
        error_msg = f'Error creating invite in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

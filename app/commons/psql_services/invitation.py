# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi_sqlalchemy import db

from app.logger import logger
from app.models.api_response import EAPIResponseCode
from app.models.sql_invitation import InvitationModel
from app.resources.error_handler import APIException


def query_invites(query: dict) -> list:
    try:
        invites = db.session.query(InvitationModel).filter_by(**query).all()
    except Exception as e:
        error_msg = f'Error querying invite in psql: {str(e)}'
        logger.error(error_msg)
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
        logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

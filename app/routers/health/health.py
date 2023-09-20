# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import LoggerFactory
from fastapi import APIRouter
from fastapi.responses import Response
from fastapi_sqlalchemy import db
from fastapi_utils import cbv
from sqlalchemy import create_engine

from app.config import ConfigSettings
from app.models.sql_events import UserEventModel
from app.models.sql_invitation import InvitationModel
from app.resources.error_handler import APIException

logger = LoggerFactory(
    'api_health',
    level_default=ConfigSettings.LOG_LEVEL_DEFAULT,
    level_file=ConfigSettings.LOG_LEVEL_FILE,
    level_stdout=ConfigSettings.LOG_LEVEL_STDOUT,
    level_stderr=ConfigSettings.LOG_LEVEL_STDERR,
).get_logger()

router = APIRouter(tags=['Health'])


def psql_health_check() -> bool:
    try:
        create_engine(ConfigSettings.RDS_DB_URI, echo=True)
    except Exception as e:
        error_msg = f"Couldn't connect to postgres: {e}"
        logger.error(error_msg)
        raise APIException(error_msg=error_msg, status_code=503)

    try:
        db.session.query(UserEventModel).first()
    except Exception as e:
        error_msg = f"Couldn't query user_event table: {e}"
        logger.error(error_msg)
        raise APIException(error_msg=error_msg, status_code=503)
    try:
        db.session.query(InvitationModel).first()
    except Exception as e:
        error_msg = f"Couldn't query invitation table: {e}"
        logger.error(error_msg)
        raise APIException(error_msg=error_msg, status_code=503)
    return True


@cbv.cbv(router)
class Health:
    @router.get(
        '/health',
        summary='Health check',
    )
    async def get(self):
        psql_health_check()
        return Response(status_code=204)

# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Tuple

from fastapi_sqlalchemy import db
from sqlalchemy import or_

from app.components.identity.crud import IdentityCRUD
from app.logger import logger
from app.models.api_response import EAPIResponseCode
from app.models.sql_events import UserEventModel
from app.resources.error_handler import APIException


def query_events(query: dict, page: int, page_size: int, order_type: str, order_by: str) -> Tuple[list, int]:
    try:
        event_query = db.session.query(UserEventModel)
        for key, value in query.items():
            if key == 'project_code':
                event_query = event_query.filter(
                    or_(
                        UserEventModel.detail['project_code'].as_string() == value,
                        UserEventModel.event_type.in_(['ACCOUNT_DISABLE', 'ACCOUNT_ACTIVATED']),
                    )
                )
            elif key == 'invitation_id':
                event_query = event_query.filter(UserEventModel.detail['invitation_id'].as_string() == value)
            else:
                event_query = event_query.filter(getattr(UserEventModel, key) == value)
        if order_type == 'desc':
            order_by = getattr(UserEventModel, order_by).desc()
        else:
            order_by = getattr(UserEventModel, order_by).asc()
        event_query = event_query.order_by(order_by)
        total = event_query.count()
        event_query = event_query.limit(page_size).offset(page * page_size)
        events = event_query.all()
    except Exception as e:
        error_msg = f'Error querying events in psql: {str(e)}'
        logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
    return events, total


async def create_event(model_data: dict, *, identity_crud: IdentityCRUD) -> UserEventModel:
    if not model_data.get('operator_id') and model_data.get('operator'):
        user = await identity_crud.get_user_by_username(model_data['operator'])
        model_data['operator_id'] = str(user['id'])
    if not model_data.get('target_user_id') and model_data.get('target_user'):
        user = await identity_crud.get_user_by_username(model_data['target_user'])
        model_data['target_user_id'] = str(user['id'])

    model_data = {k: v for k, v in model_data.items() if v}

    if not model_data.get('operator_id'):
        model_data['operator_id'] = None

    try:
        event = UserEventModel(**model_data)
        db.session.add(event)
        db.session.commit()
    except Exception as e:
        error_msg = f'Error creating event in psql: {str(e)}'
        logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
    return event


def update_event(query: dict, update_data: dict) -> dict:
    event_query = db.session.query(UserEventModel)
    for key, value in query.items():
        if key == 'invitation_id':
            event_query = event_query.filter(UserEventModel.detail['invitation_id'].as_string() == value)
        else:
            event_query = event_query.filter(getattr(UserEventModel, key) == value)
    event = event_query.first()
    if not event:
        error_msg = f'Event not found with query: {query}'
        logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

    for key, value in update_data.items():
        setattr(event, key, value)
    db.session.commit()
    return event

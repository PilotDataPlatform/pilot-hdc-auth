# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import math

from fastapi import APIRouter
from fastapi import Depends
from fastapi_utils.cbv import cbv

from app.commons.psql_services.user_event import create_event
from app.commons.psql_services.user_event import query_events
from app.components.identity.crud import IdentityCRUD
from app.components.identity.dependencies import get_identity_crud
from app.logger import logger
from app.models.api_response import APIResponse
from app.models.events import EventGETResponse
from app.models.events import EventList
from app.models.events import EventPOST
from app.models.events import EventPOSTResponse

router = APIRouter()

_API_TAG = 'Event'


@cbv(router)
class UserEvent:
    identity_crud: IdentityCRUD = Depends(get_identity_crud)

    @router.post('/events', response_model=EventPOSTResponse, summary='Creates a new event', tags=[_API_TAG])
    async def create_event(self, data: EventPOST):
        """Create event in psql event table of actions on user account such as invites or roles changes."""
        logger.info('Called create_event')
        api_response = APIResponse()

        event_data = {
            'operator_id': data.operator_id,
            'operator': data.operator,
            'target_user_id': data.target_user_id,
            'target_user': data.target_user,
            'event_type': data.event_type,
            'detail': data.detail,
        }
        event_obj = await create_event(event_data, identity_crud=self.identity_crud)
        api_response.result = event_obj.to_dict()
        return api_response.json_response()

    @router.get('/events', response_model=EventGETResponse, summary='list events', tags=[_API_TAG])
    def list_events(self, data: EventList = Depends(EventList)):
        """Lists events from psql event table of actions on user account such as invites or roles changes."""
        logger.info('Called list_events')
        api_response = APIResponse()
        query = {}
        if data.user_id:
            query['target_user_id'] = data.user_id
        if data.project_code:
            query['project_code'] = data.project_code
        if data.invitation_id:
            query['invitation_id'] = data.invitation_id
        event_list, total = query_events(query, data.page, data.page_size, data.order_type, data.order_by)
        api_response.page = data.page
        api_response.total = total
        api_response.num_of_pages = math.ceil(total / data.page_size)
        api_response.result = [i.to_dict() for i in event_list]
        return api_response.json_response()

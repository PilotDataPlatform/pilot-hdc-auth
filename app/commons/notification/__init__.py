# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx

from app.config import ConfigSettings
from app.resources.error_handler import APIException


async def record_newsfeed_notification(data: dict):
    payload = {
        'type': 'role-change',
        'recipient_username': data['recipient_username'],
        'initiator_username': data['initiator_username'],
        'project_code': data['project_code'],
        'previous': data['previous_role'],
        'current': data['current_role'],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(ConfigSettings.NOTIFY_SERVICE + 'all/notifications/', json=payload)
    if response.status_code >= 300:
        error_msg = f'Error calling notification service: {response.json()}'
        raise APIException(status_code=response.status_code, error_msg=error_msg)

# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi_utils.cbv import cbv

from app.config import ConfigSettings
from app.models.api_response import APIResponse
from app.models.external import ExternalResponse

router = APIRouter()

_API_TAG = 'Invitation'


@cbv(router)
class Invitation:
    @router.get(
        '/invitations/external',
        response_model=ExternalResponse,
        summary='Returns whether external registration is enabled',
        tags=[_API_TAG],
    )
    async def check_external(self):
        api_response = APIResponse()
        api_response.result = {'allow_external_registration': ConfigSettings.ALLOW_EXTERNAL_REGISTRATION}
        return api_response.json_response()

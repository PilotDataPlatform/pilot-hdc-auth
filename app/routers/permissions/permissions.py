# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import LoggerFactory
from fastapi import APIRouter
from fastapi import Depends
from fastapi_utils import cbv

from app.config import ConfigSettings
from app.models.api_response import APIResponse
from app.models.api_response import EAPIResponseCode
from app.resources.error_handler import catch_internal
from app.routers.permissions.casbin import Adapter
from app.routers.permissions.dependencies import get_casbin_adapter

router = APIRouter()

_API_TAG = '/v1/authorize'
_API_NAMESPACE = 'api_authorize'
_logger = LoggerFactory(
    _API_NAMESPACE,
    level_default=ConfigSettings.LOG_LEVEL_DEFAULT,
    level_file=ConfigSettings.LOG_LEVEL_FILE,
    level_stdout=ConfigSettings.LOG_LEVEL_STDOUT,
    level_stderr=ConfigSettings.LOG_LEVEL_STDERR,
).get_logger()


@cbv.cbv(router)
class Authorize:
    @router.get('/authorize', tags=[_API_TAG], summary='check the authorization for the user')
    @catch_internal(_API_NAMESPACE)
    async def get(
        self,
        role: str,
        zone: str,
        resource: str,
        operation: str,
        project_code: str = 'pilotdefault',
        adapter: Adapter = Depends(get_casbin_adapter),
    ):
        api_response = APIResponse()

        if project_code == 'pilotdefault':
            _logger.info(f'No project code using pilot default for: {resource} - {zone} - {operation}')

        api_response.result = {'has_permission': False}
        try:
            enforcer = await adapter.get_enforcer_for_project(project_code)
            if enforcer.enforce(role, zone, resource, operation, project_code):
                api_response.result = {'has_permission': True}
                api_response.code = EAPIResponseCode.success
                _logger.info(f'Access granted for {role}, {zone}, {resource}, {operation}, {project_code}')
            else:
                _logger.info(f'Access Denied for {role}, {zone}, {resource}, {operation}, {project_code}')
        except Exception as e:
            error_msg = f'Error checking permissions - {str(e)}'
            _logger.error(error_msg)
            api_response.error_msg = error_msg
            api_response.code = EAPIResponseCode.internal_error

        return api_response.json_response()

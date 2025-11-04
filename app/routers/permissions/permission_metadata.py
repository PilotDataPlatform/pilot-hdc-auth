# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import math

from fastapi import APIRouter
from fastapi import Depends
from fastapi.concurrency import run_in_threadpool
from fastapi_utils.cbv import cbv

from app.commons.psql_services.permissions import get_casbin_rules
from app.commons.psql_services.permissions import list_permissions
from app.commons.psql_services.permissions import list_roles
from app.models.api_response import EAPIResponseCode
from app.models.permissions_schema import ListPermissions
from app.models.permissions_schema import ListPermissionsResponse
from app.models.permissions_schema import ListRoles
from app.models.permissions_schema import ListRolesResponse
from app.resources.error_handler import APIException

router = APIRouter()

_API_TAG = '/v1/permission/metadata'


@cbv(router)
class PermissionMetadata:
    """Permission Metadata view."""

    @router.get(
        '/permissions/metadata',
        response_model=ListPermissionsResponse,
        summary='List permission metadata',
        tags=[_API_TAG],
    )
    async def get(self, data: ListPermissions = Depends(ListPermissions)):
        """List permission metadata."""
        api_response = ListPermissionsResponse()

        try:
            permissions, count = await run_in_threadpool(list_permissions, data)
        except Exception as e:
            raise APIException(
                error_msg=f'Failed to query permissions metadata: {e}',
                status_code=EAPIResponseCode.internal_error.value,
            )

        results = []
        for permission in permissions:
            permission_data = permission.to_dict()
            permission_data['permissions'] = await run_in_threadpool(
                get_casbin_rules,
                resource=permission.resource,
                operation=permission.operation,
                zone=permission.zone,
                project_code=data.project_code,
            )
            permission_data['project_code'] = data.project_code
            results.append(permission_data)
        api_response.result = results
        api_response.page = data.page
        api_response.num_of_pages = math.ceil(count / data.page_size)
        api_response.total = count
        return api_response.json_response()

    @router.get(
        '/permissions/roles',
        summary='list roles in project',
        tags=[_API_TAG],
    )
    async def get_list_roles(self, data: ListRoles = Depends(ListRoles)):
        """List project roles."""
        api_response = ListRolesResponse()
        roles = await run_in_threadpool(
            list_roles,
            data.project_code,
            data.order_by,
            data.order_type,
        )
        api_response.result = roles
        return api_response.json_response()

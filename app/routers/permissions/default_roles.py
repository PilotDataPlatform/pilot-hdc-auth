# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi_sqlalchemy import db
from fastapi_utils import cbv

from app.logger import logger
from app.models.api_response import APIResponse
from app.models.api_response import EAPIResponseCode
from app.models.default_roles import CreateDefaultRoles
from app.models.permissions import CasbinRule

_engine = None

router = APIRouter()

_API_TAG = '/v1/defaultroles'
_API_NAMESPACE = 'api_authorize'


@cbv.cbv(router)
class DefaultRoles:
    @router.post('/defaultroles', tags=[_API_TAG], summary='create default roles for a project')
    def post(self, data: CreateDefaultRoles):
        api_response = APIResponse()
        try:
            default_rules = db.session.query(CasbinRule).filter(CasbinRule.v4 == 'pilotdefault')
            for rule in default_rules:
                new_rule = {
                    'ptype': 'p',
                    'v0': rule.v0,
                    'v1': rule.v1,
                    'v2': rule.v2,
                    'v3': rule.v3,
                    'v4': data.project_code,
                }
                new_rule = CasbinRule(**new_rule)
                db.session.add(new_rule)
                db.session.commit()
        except Exception as e:
            error_msg = f'Error creating default roles for {data.project_code}: {str(e)}'
            logger.error(error_msg)
            api_response.error_msg = error_msg
            api_response.code = EAPIResponseCode.internal_error.value
            return api_response.json_response()
        logger.info(f'Created roles for {data.project_code}')
        api_response.result = 'success'
        return api_response.json_response()

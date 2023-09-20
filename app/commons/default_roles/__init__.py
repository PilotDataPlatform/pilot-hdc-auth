# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi_sqlalchemy import db

from app.models.api_response import EAPIResponseCode
from app.models.permissions import CasbinRule
from app.resources.error_handler import APIException


async def create_default_roles(project_code: str):
    try:
        default_rules = db.session.query(CasbinRule).filter(CasbinRule.v4 == 'pilotdefault')
        for rule in default_rules:
            new_rule = {
                'ptype': 'p',
                'v0': rule.v0,
                'v1': rule.v1,
                'v2': rule.v2,
                'v3': rule.v3,
                'v4': project_code,
            }
            new_rule = CasbinRule(**new_rule)
            db.session.add(new_rule)
            db.session.commit()
    except Exception as e:
        error_msg = f'Error creating default roles for {project_code}: {str(e)}'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)

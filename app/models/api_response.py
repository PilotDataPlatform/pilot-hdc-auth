# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from enum import Enum

from fastapi.responses import JSONResponse
from pydantic import BaseModel


class EAPIResponseCode(Enum):
    success = 200
    internal_error = 500
    bad_request = 400
    not_found = 404
    unauthorized = 401
    forbidden = 403
    conflict = 409


class APIResponse(BaseModel):
    code: EAPIResponseCode = EAPIResponseCode.success
    error_msg: str = ''
    page: int = 0
    total: int = 1
    num_of_pages: int = 1
    result = []

    def json_response(self) -> JSONResponse:
        data = self.dict()
        if isinstance(self.code, int):
            data['code'] = self.code
            return JSONResponse(status_code=self.code, content=data)
        else:
            data['code'] = self.code.value
            return JSONResponse(status_code=self.code.value, content=data)

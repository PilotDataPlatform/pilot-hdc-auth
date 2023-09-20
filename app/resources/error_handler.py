# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from functools import wraps

from app.models.api_response import APIResponse
from app.models.api_response import EAPIResponseCode


class APIException(Exception):
    def __init__(self, status_code: int, error_msg: str):
        self.status_code = status_code
        self.content = {
            'code': self.status_code,
            'error_msg': error_msg,
            'result': '',
        }


def catch_internal(api_namespace):
    """decorator to catch internal server error."""

    def decorator(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exce:
                if type(exce) == APIException:
                    raise exce
                respon = APIResponse()
                respon.code = EAPIResponseCode.internal_error
                respon.result = None
                err_msg = api_namespace + ' ' + str(exce)
                respon.error_msg = err_msg
                return respon.json_response()

        return inner

    return decorator

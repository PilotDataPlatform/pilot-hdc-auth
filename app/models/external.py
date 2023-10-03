# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from pydantic import Field

from app.models.base_models import APIResponse


class ExternalResponse(APIResponse):
    result: dict = Field(
        {},
        example={'allow_external_registration': True},
    )
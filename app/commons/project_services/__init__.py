# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import ProjectClient

from app.config import ConfigSettings


async def get_project_by_code(code: str) -> dict:
    project_client = ProjectClient(ConfigSettings.PROJECT_SERVICE, ConfigSettings.REDIS_URL)
    project = await project_client.get(code=code)
    return await project.json()

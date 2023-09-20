# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from common import LoggerFactory
from common import ProjectClient

from app.config import ConfigSettings

logger = LoggerFactory(
    'workspace_service',
    level_default=ConfigSettings.LOG_LEVEL_DEFAULT,
    level_file=ConfigSettings.LOG_LEVEL_FILE,
    level_stdout=ConfigSettings.LOG_LEVEL_STDOUT,
    level_stderr=ConfigSettings.LOG_LEVEL_STDERR,
).get_logger()


async def add_guacamole_user(username: str, container_code: str) -> None:
    payload = {'username': username, 'container_code': container_code}
    async with httpx.AsyncClient() as client:
        response = await client.post(ConfigSettings.WORKSPACE_SERVICE + 'guacamole/users', json=payload)
    if response.status_code != 200:
        error_msg = response.json().get('error_msg')
        logger.error(f'Error adding user to guacamole, user may already exist: {error_msg}')


async def get_workbench(project_id: str, resource: str) -> dict:
    project_client = ProjectClient(ConfigSettings.PROJECT_SERVICE, ConfigSettings.REDIS_URL)
    project = await project_client.get(id=project_id)

    payload = {
        'project_code': project.code,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(ConfigSettings.PROJECT_SERVICE + '/v1/workbenches/', params=payload)
    if response.status_code != 200:
        error_msg = response.json().get('error_msg')
        logger.error(f'Error getting workbench entry: {error_msg}')
        return None
    resource_data = None
    for entry in response.json()['result']:
        if entry['resource'] == 'guacamole':
            resource_data = entry
            break
    return resource_data

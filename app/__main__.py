# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import uvicorn

from app.config import ConfigSettings

if __name__ == '__main__':
    uvicorn.run(
        'app:create_app',
        factory=True,
        host=ConfigSettings.HOST,
        port=ConfigSettings.PORT,
        workers=ConfigSettings.WORKERS,
    )

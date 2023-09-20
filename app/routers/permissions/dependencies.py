# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import create_engine

from app import get_settings
from app.config import Settings
from app.routers.permissions.casbin import Adapter


class GetCasbinAdapter:
    """Create a FastAPI callable dependency for Casbin SQLAlchemy Adapter single instance."""

    def __init__(self) -> None:
        self.instance = None

    async def __call__(self, settings: Settings = Depends(get_settings)) -> Adapter:
        """Return an instance of Casbin SQLAlchemy Adapter class."""

        if not self.instance:
            engine = create_engine(settings.RDS_DB_URI, pool_pre_ping=settings.RDS_PRE_PING)
            self.instance = await run_in_threadpool(Adapter, engine=engine)

        return self.instance


get_casbin_adapter = GetCasbinAdapter()

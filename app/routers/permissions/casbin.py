# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from pathlib import Path

from casbin import Enforcer
from casbin_sqlalchemy_adapter import Adapter as CasbinAdapter
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Query

from app.models.permissions import CasbinRule


class Filtering(BaseModel):
    """CasbinRule filtering parameters."""

    project_code: str


class Adapter(CasbinAdapter):
    """Adapter with custom filtering for enforcer."""

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine=engine, db_class=CasbinRule, filtered=True)

        self.model_path = str(Path(__file__).parent / 'model.conf')

    def filter_query(self, query: Query, filtering: Filtering) -> Query:
        """Filter rules that belong to project."""

        query = query.filter(CasbinRule.v4 == filtering.project_code)
        return query.order_by(CasbinRule.id)

    async def get_enforcer_for_project(self, project_code: str) -> Enforcer:
        """Create enforcer and load policies for project."""

        enforcer = Enforcer(model=self.model_path, adapter=self)
        filtering = Filtering(project_code=project_code)
        await run_in_threadpool(enforcer.load_filtered_policy, filtering)

        return enforcer

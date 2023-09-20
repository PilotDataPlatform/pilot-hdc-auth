# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest
from faker import Faker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permissions import CasbinRule


class CasbinRuleFactory:
    model = CasbinRule

    def __init__(self, db_session: AsyncSession, fake: Faker) -> None:
        self.session = db_session
        self.fake = fake

    async def create(
        self, *, role: str = ..., zone: str = ..., resource: str = ..., operation: str = ..., project_code: str = ...
    ) -> CasbinRule:
        if role is ...:
            role = 'contributor'

        if zone is ...:
            zone = 'greenroom'

        if resource is ...:
            resource = 'project'

        if operation is ...:
            operation = 'view'

        if project_code is ...:
            project_code = self.fake.project_code()

        rule = self.model(ptype='p', v0=role, v1=zone, v2=resource, v3=operation, v4=project_code)

        self.session.add(rule)
        await self.session.commit()

        return rule

    async def bulk_create(
        self,
        number: int,
        *,
        role: str = ...,
        zone: str = ...,
        resource: str = ...,
        operation: str = ...,
        project_code: str = ...,
    ) -> list[CasbinRule]:
        return [
            await self.create(role=role, zone=zone, resource=resource, operation=operation, project_code=project_code)
            for _ in range(number)
        ]

    async def truncate_table(self) -> None:
        statement = text(f'TRUNCATE TABLE {self.model.__table__} CASCADE')
        await self.session.execute(statement)


@pytest.fixture
async def casbin_rule_factory(db_session, fake):
    casbin_rule_factory = CasbinRuleFactory(db_session, fake)
    yield casbin_rule_factory
    await casbin_rule_factory.truncate_table()

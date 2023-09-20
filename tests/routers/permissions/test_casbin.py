# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import random

import pytest
from sqlalchemy.future import create_engine

from app.routers.permissions.casbin import Adapter


@pytest.fixture
def adapter(db) -> Adapter:
    yield Adapter(engine=create_engine(db.get_connection_url()))


class TestAdapter:
    async def test_get_enforcer_for_project_loads_policies_filtered_by_project_code(self, adapter, casbin_rule_factory):
        rules = await casbin_rule_factory.bulk_create(3)
        rule = random.choice(rules)
        project_code = rule.v4
        expected_policy = [[rule.v0, rule.v1, rule.v2, rule.v3, rule.v4]]

        enforcer = await adapter.get_enforcer_for_project(project_code)

        received_policy = enforcer.model.get_policy('p', 'p')

        assert received_policy == expected_policy

    async def test_get_enforcer_for_project_loads_empty_policies_when_project_code_does_not_exist(
        self, adapter, casbin_rule_factory, fake
    ):
        await casbin_rule_factory.bulk_create(2)
        project_code = fake.project_code()

        enforcer = await adapter.get_enforcer_for_project(project_code)

        received_policy = enforcer.model.get_policy('p', 'p')

        assert received_policy == []

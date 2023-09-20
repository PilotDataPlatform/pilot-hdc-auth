# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.fixture
def db_uri(app, db):
    postgres_uri = db.get_connection_url()

    yield postgres_uri.replace('+psycopg2', '+asyncpg')


@pytest.fixture
async def db_session(db_uri) -> AsyncSession:
    db_engine = create_async_engine(db_uri)
    autocommit_engine = db_engine.execution_options(isolation_level='AUTOCOMMIT')
    session = AsyncSession(bind=autocommit_engine, expire_on_commit=False)

    try:
        yield session
    finally:
        await session.close()

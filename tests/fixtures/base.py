from collections.abc import AsyncGenerator

import httpx
import pytest_asyncio
from fastapi import FastAPI

from pyus.app import app as pyus_app
from pyus.kit.db.sqlite import AsyncSession
from pyus.redis import Redis, get_redis
from pyus.sqlite import get_db_read_session, get_db_session


@pytest_asyncio.fixture
async def app(session: AsyncSession, redis: Redis) -> AsyncGenerator[FastAPI]:
    pyus_app.dependency_overrides[get_db_session] = lambda: session
    pyus_app.dependency_overrides[get_db_read_session] = lambda: session
    pyus_app.dependency_overrides[get_redis] = lambda: redis

    yield pyus_app

    pyus_app.dependency_overrides.pop(get_db_session)


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

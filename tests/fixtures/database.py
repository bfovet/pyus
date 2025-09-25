from collections.abc import AsyncIterator, Callable, Coroutine

import pytest
import pytest_asyncio
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_utils import create_database, database_exists, drop_database

from pyus.kit.db.models.base import Model
from pyus.kit.db.sqlite import create_async_engine


def get_database_url(driver: str = "+aiosqlite") -> str:
    return f"sqlite{driver}:///sqlite_0.db"


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def initialize_test_database() -> AsyncIterator[None]:
    sync_database_url = get_database_url("")

    if database_exists(sync_database_url):
        drop_database(sync_database_url)

    create_database(sync_database_url)

    engine = create_async_engine(
        dsn=get_database_url(),
        application_name="test_0",
    )

    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    await engine.dispose()

    yield

    drop_database(sync_database_url)


@pytest_asyncio.fixture
async def session(mocker: MockerFixture) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        dsn=get_database_url(),
        application_name="test_0",
    )
    connection = await engine.connect()
    transaction = await connection.begin()

    session = AsyncSession(bind=connection, expire_on_commit=False)

    yield session

    await transaction.rollback()
    await connection.close()
    await engine.dispose()


SaveFixture = Callable[[Model], Coroutine[None, None, None]]


def save_fixture_factory(session: AsyncSession) -> SaveFixture:
    async def _save_fixture(model: Model) -> None:
        session.add(model)
        await session.flush()

    return _save_fixture


@pytest.fixture
def save_fixture(session: AsyncSession) -> SaveFixture:
    return save_fixture_factory(session)

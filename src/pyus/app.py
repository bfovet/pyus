import contextlib
from typing import AsyncIterator, TypedDict

from fastapi import FastAPI

from pyus.api import router
from pyus.config import settings
from pyus.exception_handlers import add_exception_handlers
from pyus.kit.db.sqlite import (
    AsyncEngine,
    AsyncSessionMaker,
    Engine,
    SyncSessionMaker,
    create_async_sessionmaker,
    create_sync_sessionmaker,
)
from pyus.redis import Redis, create_redis
from pyus.sqlite import AsyncSessionMiddleware, create_async_engine, create_sync_engine


class State(TypedDict):
    async_engine: AsyncEngine
    async_sessionmaker: AsyncSessionMaker
    async_read_engine: AsyncEngine
    async_read_sessionmaker: AsyncSessionMaker
    sync_engine: Engine
    sync_sessionmaker: SyncSessionMaker

    redis: Redis


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    print("Starting pyus API")

    async_engine = async_read_engine = create_async_engine("app")
    async_sessionmaker = async_read_sessionmaker = create_async_sessionmaker(
        async_engine
    )

    sync_engine = create_sync_engine("app")
    sync_sessionmaker = create_sync_sessionmaker(sync_engine)

    redis = create_redis("app")

    yield {
        "async_engine": async_engine,
        "async_sessionmaker": async_sessionmaker,
        "async_read_engine": async_read_engine,
        "async_read_sessionmaker": async_read_sessionmaker,
        "sync_engine": sync_engine,
        "sync_sessionmaker": sync_sessionmaker,
        "redis": redis,
    }

    await redis.close(True)
    await async_engine.dispose()
    if async_read_engine is not async_engine:
        await async_read_engine.dispose()
    sync_engine.dispose()

    print("pyus API stopped")


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    if not settings.is_testing():
        app.add_middleware(AsyncSessionMiddleware)

    add_exception_handlers(app)

    app.include_router(router)

    return app


app = create_app()

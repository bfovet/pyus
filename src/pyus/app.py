import contextlib
from typing import AsyncIterator, TypedDict

from fastapi import FastAPI

from pyus.api import router
from pyus.kit.db.sqlite import AsyncEngine, AsyncSessionMaker, create_async_sessionmaker
from pyus.logging import configure as configure_logging
from pyus.logging import get_logger
from pyus.opentelemetry import (
    instrument_fastapi,
    instrument_httpx,
    instrument_sqlalchemy,
)
from pyus.redis import Redis, create_redis
from pyus.sqlite import AsyncSessionMiddleware, create_async_engine

logger = get_logger(__name__)


class State(TypedDict):
    async_engine: AsyncEngine
    async_sessionmaker: AsyncSessionMaker
    async_read_engine: AsyncEngine
    async_read_sessionmaker: AsyncSessionMaker

    redis: Redis


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    logger.info("Starting pyus API")

    async_engine = async_read_engine = create_async_engine("app")
    async_sessionmaker = async_read_sessionmaker = create_async_sessionmaker(
        async_engine
    )
    instrument_sqlalchemy(async_engine.sync_engine)

    redis = create_redis("app")

    logger.info("Pyus API started")

    yield {
        "async_engine": async_engine,
        "async_sessionmaker": async_sessionmaker,
        "async_read_engine": async_read_engine,
        "async_read_sessionmaker": async_read_sessionmaker,
        "redis": redis,
    }

    await redis.close(True)
    await async_engine.dispose()
    if async_read_engine is not async_engine:
        await async_read_engine.dispose()

    logger.info("pyus API stopped")


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    app.add_middleware(AsyncSessionMiddleware)

    app.include_router(router)

    return app


configure_logging()

app = create_app()
instrument_fastapi(app)
instrument_httpx()

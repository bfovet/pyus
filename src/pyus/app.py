import contextlib
from typing import AsyncIterator, TypedDict

from fastapi import FastAPI

from pyus.api import router
from pyus.kit.db.sqlite import AsyncEngine, AsyncSessionMaker, create_async_sessionmaker
from pyus.redis import Redis, create_redis
from pyus.sqlite import AsyncSessionMiddleware, create_async_engine


class State(TypedDict):
    async_engine: AsyncEngine
    async_sessionmaker: AsyncSessionMaker
    async_read_engine: AsyncEngine
    async_read_sessionmaker: AsyncSessionMaker

    redis: Redis


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    print("Starting pyus API")

    async_engine = async_read_engine = create_async_engine("app")
    async_sessionmaker = async_read_sessionmaker = create_async_sessionmaker(
        async_engine
    )

    redis = create_redis("app")

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

    print("pyus API stopped")


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    app.add_middleware(AsyncSessionMiddleware)

    app.include_router(router)

    return app


app = create_app()

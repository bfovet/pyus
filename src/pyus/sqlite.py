from collections.abc import AsyncGenerator
from typing import Literal, TypeAlias

from fastapi import Request
from sqlalchemy import Engine
from starlette.types import ASGIApp, Receive, Scope, Send

from pyus.config import settings
from pyus.kit.db.sqlite import (
    AsyncEngine,
    AsyncReadSession,
    AsyncReadSessionMaker,
    AsyncSession,
    AsyncSessionMaker,
)
from pyus.kit.db.sqlite import create_async_engine as _create_async_engine
from pyus.kit.db.sqlite import create_sync_engine as _create_sync_engine

ProcessName: TypeAlias = Literal["app", "worker", "scheduler", "script"]


def create_async_engine(process_name: ProcessName) -> AsyncEngine:
    return _create_async_engine(
        dsn=settings.SQLITE_HOST,
        application_name=f"development.{process_name}",
        debug=True,
        check_same_thread=False,
    )


def create_async_read_engine(process_name: ProcessName) -> AsyncEngine:
    return _create_async_engine(
        dsn=settings.SQLITE_HOST,
        application_name=f"development.{process_name}",
        debug=True,
        check_same_thread=False,
    )


def create_sync_engine(process_name: ProcessName) -> Engine:
    return _create_sync_engine(
        dsn=settings.SYNC_SQLITE_HOST,
        application_name=f"development.{process_name}",
        debug=True,
        check_same_thread=False,
    )


class AsyncSessionMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        sessionmaker: AsyncSessionMaker = scope["state"]["async_sessionmaker"]
        async with sessionmaker() as session:
            scope["state"]["async_session"] = session
            await self.app(scope, receive, send)


async def get_db_sessionmaker(request: Request) -> AsyncSessionMaker:
    return request.state.async_sessionmaker


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession]:
    try:
        session = request.state.async_session
    except AttributeError as e:
        raise RuntimeError(
            "Session is not present in the request state. "
            "Did you forget to add AsyncSessionMiddleware?"
        ) from e

    try:
        yield session
    except:
        await session.rollback()
        raise
    else:
        await session.commit()


async def get_db_read_session(request: Request) -> AsyncGenerator[AsyncReadSession]:
    sessionmaker: AsyncReadSessionMaker = request.state.async_read_sessionmaker
    async with sessionmaker() as session:
        yield session


__all__ = [
    "AsyncEngine",
    "AsyncSession",
    "AsyncReadSession",
    "create_async_engine",
    "create_async_read_engine",
    "create_sync_engine",
    "get_db_session",
    "get_db_read_session",
    "get_db_sessionmaker",
]

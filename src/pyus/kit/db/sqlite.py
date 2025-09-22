from typing import Any, NewType, TypeAlias

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine

AsyncReadSession = NewType("AsyncReadSession", _AsyncSession)
"""
A type alias for read-only database sessions.

This creates a distinct type from AsyncSession that can be used to enforce
read-only operations in the type system. While functionally identical to
AsyncSession, using AsyncReadSession signals intent for read-only database
access and helps prevent accidental writes in read-only contexts.
"""

AsyncSession = NewType("AsyncSession", AsyncReadSession)
"""
A type alias for read-write database sessions.

This creates a distinct type from AsyncReadSession that can be used to enforce
read-write operations in the type system. While functionally identical to
AsyncReadSession, using AsyncSession signals intent for read-write database
access and helps prevent accidental reads in write-only contexts.
"""


def create_async_engine(
    *,
    dsn: str,
    application_name: str | None = None,
    debug: bool = False,
    check_same_thread: bool = False,
) -> AsyncEngine:
    connect_args: dict[str, Any] = {}
    # if application_name is not None:
    #     connect_args["server_settings"] = {"application_name": application_name}
    if check_same_thread is not None:
        connect_args["check_same_thread"] = check_same_thread

    return _create_async_engine(
        dsn,
        echo=debug,
        connect_args=connect_args,
    )


AsyncSessionMaker: TypeAlias = async_sessionmaker[AsyncSession]
AsyncReadSessionMaker: TypeAlias = async_sessionmaker[AsyncReadSession]


def create_async_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, autocommit=False, autoflush=False)  # pyright: ignore[reportReturnType]

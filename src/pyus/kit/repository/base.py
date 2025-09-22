from datetime import datetime
from typing import Any, Protocol, Self

from sqlalchemy import Select, select
from sqlalchemy.orm import Mapped

from pyus.kit.db.sqlite import AsyncReadSession, AsyncSession
from pyus.kit.utils import utc_now


class ModelDeletedAtProtocol(Protocol):
    deleted_at: Mapped[datetime | None]


class RepositoryProtocol[M](Protocol):
    model: type[M]

    async def get_one_or_none(self, statement: Select[tuple[M]]) -> M | None: ...

    def get_base_statement(self) -> Select[tuple[M]]: ...

    async def create(self, object: M, *, flush: bool = False) -> M: ...

    async def update(
        self,
        object: M,
        *,
        update_dict: dict[str, Any] | None = None,
        flush: bool = False,
    ) -> M: ...


class RepositoryBase[M]:
    model: type[M]

    def __init__(self, session: AsyncSession | AsyncReadSession) -> None:
        self.session = session

    async def get_one_or_none(self, statement: Select[tuple[M]]) -> M | None:
        result = await self.session.execute(statement)
        return result.unique().scalar_one_or_none()

    def get_base_statement(self) -> Select[tuple[M]]:
        return select(self.model)

    async def create(self, object: M, *, flush: bool = False) -> M:
        self.session.add(object)

        if flush:
            await self.session.flush()

        return object

    async def update(
        self,
        object: M,
        *,
        update_dict: dict[str, Any] | None = None,
        flush: bool = False,
    ) -> M:
        if update_dict is not None:
            for attr, value in update_dict.items():
                setattr(object, attr, value)

        self.session.add(object)

        if flush:
            await self.session.flush()

        return object

    @classmethod
    def from_session(cls, session: AsyncSession | AsyncReadSession) -> Self:
        return cls(session)


class RepositorySoftDeletionProtocol[MODEL_DELETED_AT: ModelDeletedAtProtocol](
    RepositoryProtocol[MODEL_DELETED_AT], Protocol
):
    def get_base_statement(
        self, *, include_deleted: bool = False
    ) -> Select[tuple[MODEL_DELETED_AT]]: ...

    async def soft_delete(
        self, object: MODEL_DELETED_AT, *, flush: bool = False
    ) -> MODEL_DELETED_AT: ...


class RepositorySoftDeletionMixin[MODEL_DELETED_AT: ModelDeletedAtProtocol]:
    def get_base_statement(
        self: RepositoryProtocol[MODEL_DELETED_AT],
        *,
        include_deleted: bool = False,
    ) -> Select[tuple[MODEL_DELETED_AT]]:
        statement = super().get_base_statement()  # type: ignore[safe-super]
        if not include_deleted:
            statement = statement.where(self.model.deleted_at.is_(None))
        return statement

    async def soft_delete(
        self: RepositoryProtocol[MODEL_DELETED_AT],
        object: MODEL_DELETED_AT,
        *,
        flush: bool = False,
    ) -> MODEL_DELETED_AT:
        return await self.update(
            object, update_dict={"deleted_at": utc_now()}, flush=flush
        )

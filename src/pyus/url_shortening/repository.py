from uuid import UUID

from pyus.kit.repository.base import RepositoryBase, RepositorySoftDeletionMixin
from pyus.models.url import ShortenedUrl


class ShortenedUrlRepository(
    RepositorySoftDeletionMixin[ShortenedUrl], RepositoryBase[ShortenedUrl]
):
    model = ShortenedUrl

    async def get_by_id(self, id: UUID):
        statement = self.get_base_statement().where(ShortenedUrl.id == id)
        return await self.get_one_or_none(statement)

    async def get_by_short_code(self, short_code: str):
        statement = self.get_base_statement().where(
            ShortenedUrl.short_code == short_code
        )
        return await self.get_one_or_none(statement)

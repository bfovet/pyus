from pyus.kit.db.sqlite import AsyncReadSession, AsyncSession
from pyus.kit.id import generate_short_code
from pyus.models.url import ShortenedUrl
from pyus.redis import Redis
from pyus.url_shortening.repository import ShortenedUrlRepository
from pyus.url_shortening.schemas import ShortenedUrlCreate


class ShortenedUrlService:
    async def get(
        self, session: AsyncReadSession, short_code: str
    ) -> ShortenedUrl | None:
        repository = ShortenedUrlRepository.from_session(session)
        statement = repository.get_base_statement().where(
            ShortenedUrl.short_code == short_code
        )
        return await repository.get_one_or_none(statement)

    async def create(
        self, session: AsyncSession, redis: Redis, create_schema: ShortenedUrlCreate
    ) -> ShortenedUrl:
        repository = ShortenedUrlRepository.from_session(session)

        short_code = await generate_short_code(create_schema.original_url, redis)

        url = await repository.create(
            ShortenedUrl(
                short_code=short_code,
                **create_schema.model_dump(),
            ),
            flush=True,
        )

        await session.flush()

        return url


url = ShortenedUrlService()

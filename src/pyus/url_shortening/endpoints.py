from fastapi import APIRouter, Depends, status

from pyus.exceptions import ResourceExpired, ResourceNotFound
from pyus.kit.db.sqlite import AsyncReadSession, AsyncSession
from pyus.models.url import ShortenedUrl
from pyus.openapi import APITag
from pyus.redis import Redis, get_redis
from pyus.sqlite import get_db_read_session, get_db_session
from pyus.url_shortening.schemas import ShortenedUrl as ShortenedUrlSchema
from pyus.url_shortening.schemas import ShortenedUrlCreate
from pyus.url_shortening.service import url as url_service

router = APIRouter(prefix="/urls", tags=["urls", APITag.public])

UrlNotFound = {
    "description": "URL not found.",
    "model": ResourceNotFound.schema(),
}

UrlExpired = {
    "description": "URL has expired.",
    "model": ResourceExpired.schema(),
}


@router.post(
    "/",
    summary="Create Shortened URL",
    response_model=ShortenedUrlSchema,
    status_code=status.HTTP_201_CREATED,
    responses={201: {"description": "Shortened URL created."}},
)
async def create(
    url_create: ShortenedUrlCreate,
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
) -> ShortenedUrl:
    """Create a shortened URL."""
    return await url_service.create(session, redis, url_create)


@router.get(
    "/{short_code}",
    summary="Get Shortened URL",
    response_model=ShortenedUrlSchema,
    responses={404: UrlNotFound},
)
async def get(
    short_code: str,
    session: AsyncReadSession = Depends(get_db_read_session),
) -> ShortenedUrl:
    """Get a Shortened URL by its short code."""
    url = await url_service.get(session, short_code)

    if url is None:
        raise ResourceNotFound()

    return url

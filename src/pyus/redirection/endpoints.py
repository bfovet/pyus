from datetime import timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse

from pyus.exceptions import ResourceExpired, ResourceNotFound
from pyus.kit.db.sqlite import AsyncReadSession
from pyus.kit.utils import utc_now
from pyus.logging import get_logger
from pyus.openapi import APITag
from pyus.redis import Redis, get_redis
from pyus.sqlite import get_db_read_session
from pyus.url_shortening.endpoints import UrlExpired, UrlNotFound
from pyus.url_shortening.service import url as url_service

logger = get_logger(__name__)


router = APIRouter(prefix="", tags=["urls", APITag.public])


@router.get(
    "/{short_code}",
    summary="Redirect to original URL",
    response_class=RedirectResponse,
    status_code=status.HTTP_302_FOUND,
    responses={404: UrlNotFound, 410: UrlExpired},
)
async def redirect(
    short_code: str,
    session: AsyncReadSession = Depends(get_db_read_session),
    redis: Redis = Depends(get_redis),
) -> str:
    """Redirect to an original URL by its short code."""
    logger.info(
        "Processing redirection request", short_code=short_code, endpoint="redirect"
    )

    if (cached_url := await redis.get(short_code)) is not None:
        logger.info(
            "Cache hit for redirection", short_code=short_code, original_url=cached_url
        )
        return cached_url

    logger.info("Cache miss for redirection", short_code=short_code)

    url = await url_service.get(session, short_code)

    if url is None:
        logger.warning("URL not found for redirection", short_code=short_code)
        raise ResourceNotFound()

    # FIXME(bf, 2025-09-27): url.expires_at should be
    # timezone-aware but does not seem to be
    url.expires_at = url.expires_at.replace(tzinfo=timezone.utc)

    if url.expires_at is not None and utc_now() >= url.expires_at:
        logger.warning(
            "URL expired for redirection",
            short_code=short_code,
            expires_at=url.expires_at.isoformat(),
        )
        raise ResourceExpired()

    ex = (url.expires_at - utc_now()) if url.expires_at is not None else 3600
    await redis.set(url.short_code, url.original_url, ex=ex)
    logger.info("URL cached for future redirections", short_code=short_code, ttl=ex)

    logger.info(
        "Redirection completed successfully",
        short_code=short_code,
        url_id=str(url.id),
        original_url=url.original_url,
    )

    return url.original_url

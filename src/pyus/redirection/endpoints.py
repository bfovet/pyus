from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse

from pyus.exceptions import ResourceNotFound
from pyus.kit.db.sqlite import AsyncReadSession
from pyus.openapi import APITag
from pyus.redis import Redis, get_redis
from pyus.sqlite import get_db_read_session
from pyus.url_shortening.endpoints import UrlNotFound
from pyus.url_shortening.service import url as url_service

router = APIRouter(prefix="", tags=["urls", APITag.public])


@router.get(
    "/{short_code}",
    summary="Redirect to original URL",
    response_class=RedirectResponse,
    status_code=status.HTTP_302_FOUND,
    responses={404: UrlNotFound},
)
async def redirect(
    short_code: str,
    session: AsyncReadSession = Depends(get_db_read_session),
    redis: Redis = Depends(get_redis),
) -> str:
    """Redirect to an original URL by its short code."""
    if (cached_url := await redis.get(short_code)) is not None:
        return cached_url

    url = await url_service.get(session, short_code)

    if url is None:
        raise ResourceNotFound()

    await redis.set(url.short_code, url.original_url, ex=3600)

    return url.original_url

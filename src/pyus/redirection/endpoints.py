from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse

from pyus.exceptions import ResourceNotFound
from pyus.kit.db.sqlite import AsyncReadSession
from pyus.openapi import APITag
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
    short_code: str, session: AsyncReadSession = Depends(get_db_read_session)
) -> str:
    """Redirect to an original URL by its short code."""
    url = await url_service.get(session, short_code)

    if url is None:
        raise ResourceNotFound()

    return url.original_url

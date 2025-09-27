from fastapi import APIRouter, Depends, status
from opentelemetry import baggage

from pyus.exceptions import ResourceExpired, ResourceNotFound
from pyus.kit.db.sqlite import AsyncReadSession, AsyncSession
from pyus.logging import get_logger
from pyus.models.url import ShortenedUrl
from pyus.openapi import APITag
from pyus.opentelemetry import get_tracer
from pyus.redis import Redis, get_redis
from pyus.sqlite import get_db_read_session, get_db_session
from pyus.url_shortening.schemas import ShortenedUrl as ShortenedUrlSchema
from pyus.url_shortening.schemas import ShortenedUrlCreate
from pyus.url_shortening.service import url as url_service

tracer = get_tracer(__name__)
logger = get_logger(__name__)


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

    ctx = baggage.set_baggage("endpoint", "create_url")
    ctx = baggage.set_baggage("operation", "url_shortening", ctx)

    result: ShortenedUrl
    with tracer.start_as_current_span(
        "POST /api/v1/urls",
        context=ctx,
        attributes={
            "http.method": "POST",
            "http.route": "/api/v1/urls",
            "url.original": str(url_create.original_url),
        },
    ) as span:
        logger.info(
            "Creating shortened URL",
            original_url=url_create.original_url,
            expires_at=url_create.expires_at.isoformat()
            if url_create.expires_at
            else None,
            endpoint="create_url",
        )

        result = await url_service.create(session, redis, url_create)

        span.set_attributes(
            {
                "http.status_code": 201,
                "url.id": str(result.id),
                "url.short_code": result.short_code,
            }
        )

        logger.info(
            "Shortened URL created successfully",
            url_id=str(result.id),
            short_code=result.short_code,
            original_url=result.original_url,
            expires_at=result.expires_at,
        )

    return result


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

    ctx = baggage.set_baggage("endpoint", "get_url")
    ctx = baggage.set_baggage("operation", "url_retrieval", ctx)

    with tracer.start_as_current_span(
        f"GET /api/v1/urls/{short_code}",
        context=ctx,
        attributes={
            "http.method": "GET",
            "http.route": "/api/v1/urls/{short_code}",
            "url.short_code": short_code,
        },
    ) as span:
        logger.info("Retrieving URL", short_code=short_code, endpoint="get_url")

        url = await url_service.get(session, short_code)

        if url is None:
            span.set_attribute("http.status_code", 404)
            logger.warning("URL not found", short_code=short_code)
            raise ResourceNotFound()

        span.set_attributes(
            {
                "http.status_code": 200,
                "url.id": str(url.id),
                "url.original": url.original_url,
            }
        )

        logger.info(
            "URL retrieved successfully",
            short_code=short_code,
            url_id=str(url.id),
            original_url=url.original_url,
        )

        return url

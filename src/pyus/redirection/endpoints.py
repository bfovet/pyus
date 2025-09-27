from datetime import timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse
from opentelemetry import baggage
from opentelemetry.metrics import Counter

from pyus.exceptions import ResourceExpired, ResourceNotFound
from pyus.kit.db.sqlite import AsyncReadSession
from pyus.kit.utils import utc_now
from pyus.logging import get_logger
from pyus.openapi import APITag
from pyus.opentelemetry import get_tracer, get_meter
from pyus.redis import Redis, get_redis
from pyus.sqlite import get_db_read_session
from pyus.url_shortening.endpoints import UrlExpired, UrlNotFound
from pyus.url_shortening.service import url as url_service

tracer = get_tracer(__name__)
meter = get_meter(__name__)
logger = get_logger(__name__)


router = APIRouter(prefix="", tags=["urls", APITag.public])


# Custom metrics for redirections
redirect_counter: Counter = meter.create_counter(
    name="redirections_total",
    description="Total number of redirections",
    unit="1"
)

cache_hit_counter: Counter = meter.create_counter(
    name="cache_hits_total",
    description="Total number of cache hits",
    unit="1"  
)


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

    ctx = baggage.set_baggage("endpoint", "redirect")
    ctx = baggage.set_baggage("operation", "url_redirection", ctx)

    with tracer.start_as_current_span(
        f"GET /{short_code}",
        context=ctx,
        attributes={
            "http.method": "GET",
            "http.route": "/{short_code}",
            "url.short_code": short_code,
        },
    ) as span:
        logger.info(
            "Processing redirection request", short_code=short_code, endpoint="redirect"
        )

        cached_url: str | None = None
        with tracer.start_as_current_span("redis_cache_lookup") as cache_span:
            if (cached_url := await redis.get(short_code)) is not None:
                cache_span.set_attributes(
                    {"cache.hit": cached_url is not None, "cache.key": short_code}
                )
                cache_hit_counter.add(1, attributes={"status": "hit"})
                logger.info(
                    "Cache hit for redirection",
                    short_code=short_code,
                    original_url=cached_url,
                )
            else:
                cache_hit_counter.add(1, attributes={"status": "miss"})
                logger.info("Cache miss for redirection", short_code=short_code)

        if cached_url is not None:
            redirect_counter.add(
                1,
                attributes={
                    "status": "success",
                    "cache": "hit"
                }
            )
            span.set_attributes(
                {"http.status_code": 302, "url.original": cached_url, "cache.hit": True}
            )

            return cached_url

        with tracer.start_as_current_span("database_lookup") as db_span:
            url = await url_service.get(session, short_code)
            db_span.set_attributes(
                {"db.operation": "select", "url.found": url is not None}
            )

        if url is None:
            redirect_counter.add(
                1,
                attributes={
                    "status": "not_found",
                    "cache": "miss"
                }
            )
            span.set_attribute("http.status_code", 404)
            logger.warning("URL not found for redirection", short_code=short_code)
            raise ResourceNotFound()

        # FIXME(bf, 2025-09-27): url.expires_at should be
        # timezone-aware but does not seem to be
        url.expires_at = url.expires_at.replace(tzinfo=timezone.utc)

        if url.expires_at is not None and utc_now() >= url.expires_at:
            redirect_counter.add(
                1,
                attributes={
                    "status": "expired", 
                    "cache": "miss"
                }
            )
            span.set_attributes(
                {
                    "http.status_code": 410,
                    "url.expired": True,
                    "url.expires_at": url.expires_at.isoformat(),
                }
            )
            logger.warning(
                "URL expired for redirection",
                short_code=short_code,
                expires_at=url.expires_at.isoformat(),
            )
            raise ResourceExpired()

        with tracer.start_as_current_span("cache_url") as cache_span:
            ex = (url.expires_at - utc_now()) if url.expires_at is not None else 3600
            await redis.set(url.short_code, url.original_url, ex=ex)
            cache_span.set_attributes(
                {
                    "cache.key": url.short_code,
                    "cache.ttl": 3600,  # TODO: actually store the ttl
                }
            )
            logger.info(
                "URL cached for future redirections", short_code=short_code, ttl=ex
            )

        redirect_counter.add(
            1,
            attributes={
                "status": "success",
                "cache": "miss"
            }
        )

        span.set_attributes(
            {
                "http.status_code": 302,
                "url.id": str(url.id),
                "url.original": url.original_url,
                "cache.hit": False,
            }
        )

        logger.info(
            "Redirection completed successfully",
            short_code=short_code,
            url_id=str(url.id),
            original_url=url.original_url,
        )

        return url.original_url

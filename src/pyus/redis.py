from typing import TYPE_CHECKING, Literal, TypeAlias

from fastapi import Request
from redis import ConnectionError, RedisError, TimeoutError
import redis.asyncio as _async_redis
from redis.asyncio.retry import Retry
from redis.backoff import default_backoff

from pyus.config import settings

# https://github.com/python/typeshed/issues/7597#issuecomment-1117551641
# Redis is generic at type checking, but not at runtime...
if TYPE_CHECKING:
    Redis = _async_redis.Redis[str]  # pyright: ignore[reportInvalidTypeArguments]
else:
    Redis = _async_redis.Redis


REDIS_RETRY_ON_ERRROR: list[type[RedisError]] = [ConnectionError, TimeoutError]
REDIS_RETRY = Retry(default_backoff(), retries=50)

ProcessName: TypeAlias = Literal["app", "rate-limit", "worker", "script"]


def create_redis(process_name: ProcessName) -> Redis:
    return _async_redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        retry_on_error=REDIS_RETRY_ON_ERRROR,
        retry=REDIS_RETRY,
        client_name=f"development.{process_name}",
    )


async def get_redis(request: Request) -> Redis:
    return request.state.redis


__all__ = [
    "Redis",
    "REDIS_RETRY_ON_ERRROR",
    "REDIS_RETRY",
    "create_redis",
    "get_redis",
]

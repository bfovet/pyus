import base64
import hashlib
from collections import deque

from pydantic import HttpUrl

from pyus.redis import Redis


class UniqueIdGenerator:
    def __init__(self):
        self._counter_key = "url_id"
        self._incr_value = 1000
        self._ids: deque = deque()

    async def get_ids(self, redis: Redis) -> deque:
        if not self._ids:
            print(f"Requesting {self._incr_value} values from key generation service")
            self._ids = await self._get_ids(redis)

        return self._ids

    async def _get_ids(self, redis: Redis) -> deque:
        pipe = redis.pipeline()
        pipe.setnx(self._counter_key, 0)
        pipe.get(self._counter_key)
        pipe.incrby(self._counter_key, self._incr_value)
        res = await pipe.execute()

        return deque(range(int(res[1]), res[-1]))


unique_id_generator = UniqueIdGenerator()


async def get_next_id(redis: Redis):
    next_ids = await unique_id_generator.get_ids(redis)
    return next_ids.popleft()


def generate_short_code_with_id(url: HttpUrl, id: int) -> str:
    hash_object = hashlib.sha512(f"{url}{id}".encode())
    hash_base64 = base64.urlsafe_b64encode(str.encode(hash_object.hexdigest())).decode(
        "utf-8"
    )
    return hash_base64[:7]


async def generate_short_code(url: HttpUrl, redis: Redis) -> str:
    id = await get_next_id(redis)
    hash_key = generate_short_code_with_id(url, id)
    return hash_key

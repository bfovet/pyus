import uuid

import pytest
from httpx import AsyncClient

from pyus.models import ShortenedUrl


@pytest.mark.asyncio
class TestGetUrl:
    async def test_not_existing(self, client: AsyncClient):
        response = await client.get(f"/api/v1/urls/{uuid.uuid4()}")

        assert response.status_code == 404

    async def test_valid(self, client: AsyncClient, url: ShortenedUrl) -> None:
        response = await client.get(f"/api/v1/urls/{url.id}")

        assert response.status_code == 200

        json = response.json()
        assert json["short_code"] == url.short_code

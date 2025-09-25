import pytest
import pytest_asyncio
from httpx import AsyncClient

from pyus.models import ShortenedUrl
from tests.fixtures.database import SaveFixture
from tests.fixtures.random_objects import create_url


@pytest_asyncio.fixture
async def urls(
    save_fixture: SaveFixture, url: ShortenedUrl
) -> list[ShortenedUrl]:
    return [
        await create_url(save_fixture, original_url=url.original_url, short_code=url.short_code)
    ]


@pytest.mark.asyncio
class TestGetUrl:
    async def test_not_existing(self, client: AsyncClient):
        response = await client.get("/api/v1/urls/XXX")

        assert response.status_code == 404

    async def test_url_valid(
        self, client: AsyncClient, urls: list[ShortenedUrl]
    ) -> None:
        response = await client.get(f"/api/v1/urls/{urls[0].short_code}")

        assert response.status_code == 200

        json = response.json()
        assert json["short_code"] == urls[0].short_code

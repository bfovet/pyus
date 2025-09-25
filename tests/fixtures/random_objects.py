import uuid
from datetime import datetime

import pytest_asyncio
from dateutil.relativedelta import relativedelta

from pyus.kit.utils import utc_now
from pyus.models.url import ShortenedUrl
from tests.fixtures.database import SaveFixture


async def create_url(
    save_fixture: SaveFixture,
    *,
    expires_at: datetime | None = None,
    original_url: str = "https://foo.bar",
    short_code: str = "ABC1234",
):
    url = ShortenedUrl(
        id=uuid.uuid4(),
        expires_at=expires_at or utc_now() + relativedelta(years=1),
        original_url=original_url,
        short_code=short_code,
    )

    await save_fixture(url)
    return url


@pytest_asyncio.fixture
async def url(save_fixture: SaveFixture) -> ShortenedUrl:
    return await create_url(save_fixture)

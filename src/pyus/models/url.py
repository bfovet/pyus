from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from pyus.kit.db.models.base import RecordModel


class ShortenedUrl(RecordModel):
    __tablename__ = "urls"

    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    short_code: Mapped[str] = mapped_column(Text, nullable=False)

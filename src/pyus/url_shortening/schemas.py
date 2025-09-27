from pydantic import UUID4, AwareDatetime, Field, HttpUrl, field_validator

from pyus.kit.schemas import IDSchema, Schema, TimestampedSchema


class ShortenedUrlBase(TimestampedSchema, IDSchema):
    expires_at: AwareDatetime | None = Field(
        description="Expiration date of the URL.", default=None
    )
    id: UUID4 = Field(description="The ID of the URL.")
    original_url: HttpUrl = Field(description="Original URL.")


class ShortenedUrl(ShortenedUrlBase):
    short_code: str = Field(description="Generated short code")


class ShortenedUrlCreate(Schema):
    original_url: HttpUrl = Field(description="Original URL.")
    expires_at: AwareDatetime | None = Field(
        description="Expiration date of the URL.", default=None
    )

    @field_validator("original_url", mode="after")
    @classmethod
    def convert_url_to_string(cls, v):
        return str(v) if isinstance(v, HttpUrl) else v

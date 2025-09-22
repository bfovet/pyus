from pyus.kit.repository.base import RepositoryBase, RepositorySoftDeletionMixin
from pyus.models.url import ShortenedUrl


class ShortenedUrlRepository(
    RepositorySoftDeletionMixin[ShortenedUrl], RepositoryBase[ShortenedUrl]
):
    model = ShortenedUrl

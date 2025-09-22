from fastapi import APIRouter

from pyus.redirection.endpoints import router as redirection_router
from pyus.url_shortening.endpoints import router as url_router

router = APIRouter(prefix="/api/v1")

# /
router.include_router(redirection_router)

# /urls
router.include_router(url_router)

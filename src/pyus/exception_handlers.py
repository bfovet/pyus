from urllib.parse import urlencode

from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from pyus.config import settings
from pyus.exceptions import (
    PyusError,
    PyusRedirectionError,
    PyusRequestValidationError,
    ResourceNotModified,
)


async def pyus_exception_handler(request: Request, exc: PyusError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": type(exc).__name__, "detail": exc.message},
        headers=exc.headers,
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError | PyusRequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": type(exc).__name__, "detail": jsonable_encoder(exc.errors())},
    )


async def pyus_redirection_exception_handler(
    request: Request, exc: PyusRedirectionError
) -> RedirectResponse:
    error_url_params = urlencode(
        {
            "message": exc.message,
            "return_to": exc.return_to or settings.FRONTEND_DEFAULT_RETURN_PATH,
        }
    )
    error_url = f"{settings.generate_frontend_url('/error')}?{error_url_params}"
    return RedirectResponse(error_url, 303)


async def pyus_not_modified_handler(
    request: Request, exc: ResourceNotModified
) -> Response:
    return Response(status_code=exc.status_code)


def add_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        PyusRedirectionError,
        pyus_redirection_exception_handler,  # type: ignore
    )
    app.add_exception_handler(
        ResourceNotModified,
        pyus_not_modified_handler,  # type: ignore
    )

    app.add_exception_handler(
        RequestValidationError,
        request_validation_exception_handler,  # type: ignore
    )
    app.add_exception_handler(
        PyusRequestValidationError,
        request_validation_exception_handler,  # type: ignore
    )
    app.add_exception_handler(PyusError, pyus_exception_handler)  # type: ignore

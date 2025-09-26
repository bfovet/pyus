from fastapi import FastAPI
import httpx
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy import Engine


def instrument_httpx(client: httpx.AsyncClient | httpx.Client | None = None) -> None:
    if client:
        HTTPXClientInstrumentor().instrument_client(client)


def instrument_fastapi(app: FastAPI) -> None:
    FastAPIInstrumentor.instrument_app(app)


def instrument_sqlalchemy(engine: Engine) -> None:
    SQLAlchemyInstrumentor().instrument(engine=engine)

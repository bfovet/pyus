from typing import Any

import httpx
from fastapi import FastAPI
from opentelemetry import baggage, trace, metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider
from sqlalchemy import Engine

from pyus.config import settings
from pyus.redis import Redis


def add_trace_context(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add OpenTelemetry trace context to log records"""
    span = trace.get_current_span()
    if span and span.is_recording():
        span_ctx = span.get_span_context()
        event_dict["trace_id"] = f"{span_ctx.trace_id:032x}"
        event_dict["span_id"] = f"{span_ctx.span_id:016x}"

    baggage_ctx = baggage.get_all()
    if baggage_ctx:
        event_dict["baggage"] = baggage_ctx

    return event_dict


def setup_tracing() -> TracerProvider:
    tracer_provider = TracerProvider(
        resource=Resource.create(
            {
                SERVICE_NAME: "pyus",
                SERVICE_VERSION: "0.1.0",
                "environment": settings.ENV,
            }
        )
    )
    set_tracer_provider(tracer_provider)

    span_exporter = OTLPSpanExporter()

    span_processor = BatchSpanProcessor(span_exporter)
    tracer_provider.add_span_processor(span_processor)

    return tracer_provider


def setup_metrics() -> MeterProvider:
    metric_exporter = OTLPMetricExporter()

    metric_reader = PeriodicExportingMetricReader(
        exporter=metric_exporter,
        export_interval_millis=10000,
    )

    meter_provider = MeterProvider(
        resource=Resource.create(
            {
                SERVICE_NAME: "pyus",
                SERVICE_VERSION: "0.1.0",
                "environment": settings.ENV,
            }
        ),
        metric_readers=[metric_reader]
    )
    set_meter_provider(meter_provider)

    return meter_provider


def get_tracer(name: str = "pyus") -> trace.Tracer:
    """Get a tracer instance"""
    return trace.get_tracer(name)


def get_meter(name: str = "pyus") -> metrics.Meter:
    """Get a meter instance"""
    return metrics.get_meter(name)


def instrument_httpx(client: httpx.AsyncClient | httpx.Client | None = None) -> None:
    if client:
        HTTPXClientInstrumentor().instrument_client(client)


def instrument_fastapi(app: FastAPI) -> None:
    FastAPIInstrumentor.instrument_app(app)


def instrument_sqlalchemy(engine: Engine) -> None:
    SQLAlchemyInstrumentor().instrument(engine=engine)


def instrument_redis(redis: Redis) -> None:
    RedisInstrumentor().instrument_client(redis)

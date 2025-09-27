import logging.config
import uuid
from typing import Any

import structlog
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource

from pyus.config import settings
from pyus.opentelemetry import add_trace_context


class Logging[RendererType]:
    """Hubben logging configurator of `structlog` and `logging`.

    Customized implementation inspired by the following documentation:
    https://www.structlog.org/en/stable/standard-library.html#rendering-using-structlog-based-formatters-within-logging

    """

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    @classmethod
    def get_level(cls) -> str:
        return settings.LOG_LEVEL

    @classmethod
    def get_processors(cls) -> list[Any]:
        return [
            add_trace_context,
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            cls.timestamper,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.StackInfoRenderer(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            structlog.processors.JSONRenderer(),
        ]

    @classmethod
    def get_renderer(cls) -> RendererType:
        raise NotImplementedError()

    @classmethod
    def configure_stdlib(cls) -> None:
        level = cls.get_level()
        logging.config.dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": True,
                "formatters": {
                    "pyus": {
                        "()": structlog.stdlib.ProcessorFormatter,
                        "processors": [
                            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                            cls.get_renderer(),
                        ],
                        "foreign_pre_chain": [
                            structlog.contextvars.merge_contextvars,
                            structlog.stdlib.add_log_level,
                            structlog.stdlib.add_logger_name,
                            structlog.stdlib.PositionalArgumentsFormatter(),
                            structlog.stdlib.ExtraAdder(),
                            cls.timestamper,
                            structlog.processors.UnicodeDecoder(),
                            structlog.processors.StackInfoRenderer(),
                        ],
                    },
                },
                "handlers": {
                    "default": {
                        "level": level,
                        "class": "logging.StreamHandler",
                        "formatter": "pyus",
                    },
                },
                "loggers": {
                    "": {
                        "handlers": ["default"],
                        "level": level,
                        "propagate": False,
                    },
                    # Propagate third-party loggers to the root one
                    **{
                        logger: {
                            "handlers": [],
                            "propagate": True,
                        }
                        for logger in [
                            "uvicorn",
                            "sqlalchemy",
                        ]
                    },
                },
            }
        )

    @classmethod
    def configure_structlog(cls) -> None:
        structlog.configure_once(
            processors=cls.get_processors(),
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    @classmethod
    def configure(cls) -> None:
        cls.configure_stdlib()
        cls.configure_structlog()

        logger_provider = LoggerProvider(
            resource=Resource.create(
                {
                    SERVICE_NAME: "pyus",
                    SERVICE_VERSION: "0.1.0",
                    "environment": settings.ENV,
                }
            )
        )
        set_logger_provider(logger_provider)

        exporter = OTLPLogExporter()
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
        handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)

        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)


class Development(Logging[structlog.dev.ConsoleRenderer]):
    @classmethod
    def get_renderer(cls) -> structlog.dev.ConsoleRenderer:
        return structlog.dev.ConsoleRenderer(colors=True)


class Production(Logging[structlog.processors.JSONRenderer]):
    @classmethod
    def get_renderer(cls) -> structlog.processors.JSONRenderer:
        return structlog.processors.JSONRenderer()


def configure() -> None:
    if settings.is_testing():
        Development.configure()
    elif settings.is_development():
        Development.configure()
    else:
        Production.configure()


def generate_correlation_id() -> str:
    return str(uuid.uuid4())


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """Get a structlog logger instance"""
    return structlog.get_logger(name)

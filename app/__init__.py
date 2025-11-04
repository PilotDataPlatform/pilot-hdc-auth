# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import ProjectException
from common import configure_logging
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_sqlalchemy import DBSessionMiddleware
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import Settings
from app.config import get_settings
from app.resources.error_handler import APIException
from app.routers.api_registry import api_registry


def create_app(settings: Settings | None = None) -> FastAPI:
    """Initialize and configure the application."""

    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title='Service Auth',
        description='Service for user authentication and authorization',
        docs_url='/v1/api-doc',
        version=settings.VERSION,
    )

    app.add_middleware(DBSessionMiddleware, db_url=settings.RDS_DB_URI)

    app.add_middleware(
        CORSMiddleware,
        allow_origins='*',
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    @app.exception_handler(APIException)
    async def http_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.content,
        )

    @app.exception_handler(ProjectException)
    async def project_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.content,
        )

    setup_logging(settings)
    api_registry(app)
    instrument_app(app)

    return app


def setup_logging(settings: Settings) -> None:
    """Configure the application logging."""

    configure_logging(settings.LOGGING_LEVEL, settings.LOGGING_FORMAT)


def instrument_app(app) -> None:
    """Instrument the application with OpenTelemetry tracing."""

    settings = get_settings()

    if not settings.OPEN_TELEMETRY_ENABLED:
        return

    tracer_provider = TracerProvider(resource=Resource.create({SERVICE_NAME: settings.APP_NAME}))
    trace.set_tracer_provider(tracer_provider)

    jaeger_exporter = JaegerExporter(
        agent_host_name=settings.OPEN_TELEMETRY_HOST, agent_port=settings.OPEN_TELEMETRY_PORT
    )

    tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

    FastAPIInstrumentor().instrument_app(app)
    LoggingInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(service=settings.APP_NAME)
    HTTPXClientInstrumentor().instrument()

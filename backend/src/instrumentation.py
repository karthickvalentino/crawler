import logging
import os

from celery import Celery
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes


def setup_logging(service_name: str):
    """
    Sets up OpenTelemetry logging.
    """
    resource = Resource.create(
        attributes={ResourceAttributes.SERVICE_NAME: service_name}
    )

    # Create a LoggerProvider
    logger_provider = LoggerProvider(resource=resource)

    # Create an OTLPLogExporter
    log_exporter = OTLPLogExporter(
        endpoint="http://crawler_otel_collector:4317/v1/logs"
    )

    # Create a BatchLogProcessor and add the exporter
    log_processor = BatchLogRecordProcessor(log_exporter)
    logger_provider.add_log_record_processor(log_processor)

    # Create a LoggingHandler and set the LoggerProvider
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)


def instrument_application(app: FastAPI):
    """
    Instruments the FastAPI application with OpenTelemetry.
    """
    setup_logging("fastapi-app")
    resource = Resource.create(attributes={"service.name": "fastapi-app"})

    trace.set_tracer_provider(TracerProvider(resource=resource))

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otlp_endpoint:
        # If the endpoint is not set, we disable the exporter
        # This is useful for local development without the collector
        return

    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)

    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

    FastAPIInstrumentor.instrument_app(app)


def instrument_celery(celery_app: Celery):
    """
    Instruments the Celery application with OpenTelemetry.
    """
    setup_logging("celery-worker")
    CeleryInstrumentor().instrument()

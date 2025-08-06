import os

from celery import Celery
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def instrument_application(app: FastAPI):
    """
    Instruments the FastAPI application with OpenTelemetry.
    """
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
    CeleryInstrumentor().instrument()

from celery import Celery
from src.config import settings
from src.instrumentation import instrument_celery

# Define the Celery app
celery_app = Celery(
    "tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.tasks"]  # Point to the module where tasks are defined
)
instrument_celery(celery_app)

# Celery configuration
celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    # Define a dead-letter queue
    task_queues={
        "default": {
            "exchange": "default",
            "routing_key": "default"
        },
        "dead_letter": {
            "exchange": "dead_letter",
            "routing_key": "dead_letter"
        }
    },
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
)

if __name__ == "__main__":
    celery_app.start()

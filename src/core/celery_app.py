import os
from celery import Celery

# Default to dify-redis:6379/1 if not set
broker_url = os.environ.get("CELERY_BROKER_URL", "redis://dify-redis:6379/1")
result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://dify-redis:6379/1")

celery_app = Celery(
    "coreason_tasks",
    broker=broker_url,
    backend=result_backend,
    include=["src.core.tasks.agent_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Standard settings for high-concurrency IO tasks
    worker_prefetch_multiplier=1, 
)

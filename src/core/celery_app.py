import os
from celery import Celery

# Default to REDIS_URL or localhost:6379/1 if not set
default_redis = os.environ.get("REDIS_URL", "redis://localhost:6379").rstrip("/") + "/1"
broker_url = os.environ.get("CELERY_BROKER_URL", default_redis)
result_backend = os.environ.get("CELERY_RESULT_BACKEND", default_redis)

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

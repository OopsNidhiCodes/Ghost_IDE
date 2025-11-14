"""
Celery application configuration for GhostIDE
Handles asynchronous code execution tasks
"""

from celery import Celery
import os

# Create Celery app
celery_app = Celery(
    "ghostide",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=["app.services.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60,  # 60 second task timeout
    task_soft_time_limit=50,  # 50 second soft timeout
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)
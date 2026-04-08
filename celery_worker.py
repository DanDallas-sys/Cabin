from celery import Celery
from config import get_settings

settings = get_settings()

celery = Celery(
    "cabin_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Africa/Lagos",
    enable_utc=True,
    beat_schedule={
        "check-clarifications-daily": {
            "task": "tasks.check_clarifications",
            "schedule": 86400.0,   # every 24 hours
        },
    },
)

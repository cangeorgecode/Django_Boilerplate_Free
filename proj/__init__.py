# This package is imported by celery workers; do not add imports here that
# require a configured Django settings module at import time.
from .celery import app as celery_app

__all__ = ("celery_app",)

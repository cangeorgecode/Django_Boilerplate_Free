import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proj.settings")

app = Celery("proj")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Without a broker (local dev) run tasks inline so the pipeline still works
# end-to-end; on the server, set CELERY_BROKER_URL (Redis) and jobs go async.
if not app.conf.broker_url:
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True

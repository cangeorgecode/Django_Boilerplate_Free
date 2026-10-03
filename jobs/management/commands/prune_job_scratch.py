import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from jobs.models import Job
from uploads.models import MediaAsset


class Command(BaseCommand):
    help = "Prune job scratch dirs for finished jobs and rejected upload objects."

    def add_arguments(self, parser):
        parser.add_argument(
            "--older-than-days",
            type=int,
            default=7,
            help="Only prune jobs finished more than N days ago (default 7).",
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options["older_than_days"])
        jobs = Job.objects.filter(
            status__in=[Job.Status.DONE, Job.Status.FAILED], updated_at__lt=cutoff
        )
        removed_dirs = 0
        for job in jobs.iterator():
            path = os.path.join(settings.JOB_WORK_DIR, str(job.pk))
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
                removed_dirs += 1
        self.stdout.write(f"pruned {removed_dirs} job scratch dir(s)")

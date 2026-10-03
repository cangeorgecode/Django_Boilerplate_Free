import os
import shutil
import sys

from django.core.management.base import BaseCommand

from uploads.models import MediaAsset
from uploads import services


class Command(BaseCommand):
    help = "Validate pending media uploads with ffprobe and clean up stale ones."

    def handle(self, *args, **options):
        if not services.ffprobe_available():
            self.stderr.write("ffprobe not found — install ffmpeg. Nothing done.")
            sys.exit(1)

        pending = MediaAsset.objects.filter(status=MediaAsset.Status.PENDING)
        validated = rejected = 0
        for asset in pending.iterator():
            services.validate_asset_media(asset)
            if asset.status == MediaAsset.Status.VALIDATED:
                validated += 1
            else:
                rejected += 1
        self.stdout.write(f"validated={validated} rejected={rejected}")

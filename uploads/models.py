import uuid

from django.contrib.auth.models import User
from django.db import models


def generate_object_key(user_pk, extension):
    """Object keys are server-generated UUIDs under a per-user prefix — the
    client never chooses the key, so path traversal is impossible."""
    return f"uploads/{user_pk}/{uuid.uuid4().hex}{extension}"


class MediaAsset(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"       # uploaded, awaiting ffprobe validation
        VALIDATED = "validated"   # confirmed to be real, sane media
        REJECTED = "rejected"     # failed validation

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="media_assets")
    object_key = models.CharField(max_length=512, unique=True)
    original_name = models.CharField(max_length=255, blank=True, default="")
    content_type = models.CharField(max_length=120, blank=True, default="")
    size = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reject_reason = models.CharField(max_length=255, blank=True, default="")
    duration_seconds = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.object_key} ({self.status})"

    @property
    def display_name(self):
        return self.original_name or self.object_key.rsplit("/", 1)[-1]

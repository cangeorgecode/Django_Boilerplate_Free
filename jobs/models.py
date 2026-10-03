from django.contrib.auth.models import User
from django.db import models

from uploads.models import MediaAsset


class Job(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued"
        TRANSCRIBING = "transcribing"
        PLANNING = "planning"
        VOICING = "voicing"
        RENDERING = "rendering"
        DONE = "done"
        FAILED = "failed"

    STAGE_ORDER = {
        Status.QUEUED: 5,
        Status.TRANSCRIBING: 20,
        Status.PLANNING: 40,
        Status.VOICING: 60,
        Status.RENDERING: 80,
        Status.DONE: 100,
        Status.FAILED: 100,
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs")
    footage = models.ForeignKey(
        MediaAsset, on_delete=models.PROTECT, related_name="jobs", null=True, blank=True
    )
    script = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    progress = models.PositiveSmallIntegerField(default=0)
    error = models.CharField(max_length=500, blank=True, default="")
    credits_cost = models.PositiveSmallIntegerField(default=1)
    # Per-stage resource usage for the cost report: {"deepgram_minutes": x,
    # "tts_chars": y, "llm_tokens": z, "ffmpeg_seconds": s}
    cost_breakdown = models.JSONField(default=dict, blank=True)
    logs = models.JSONField(default=list, blank=True)
    output = models.ForeignKey(
        MediaAsset, on_delete=models.SET_NULL, related_name="jobs_as_output",
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"job {self.pk} ({self.status}) for {self.user}"

    def log(self, message):
        self.logs = (self.logs or []) + [message]
        self.save(update_fields=["logs"])

    def set_stage(self, status, progress=None):
        self.status = status
        if progress is not None:
            self.progress = progress
        else:
            self.progress = self.STAGE_ORDER.get(status, self.progress)
        self.save(update_fields=["status", "progress", "updated_at"])

    def fail(self, error):
        self.status = self.Status.FAILED
        self.progress = 100
        self.error = error[:500]
        self.save(update_fields=["status", "progress", "error", "updated_at"])

    def work_dir(self):
        from django.conf import settings
        import os

        path = os.path.join(settings.JOB_WORK_DIR, str(self.pk))
        os.makedirs(path, exist_ok=True)
        return path

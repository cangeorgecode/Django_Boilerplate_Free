import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from billing.models import CreditAccount, CreditTransaction
from uploads.models import MediaAsset

from .models import Job

TEST_SETTINGS = override_settings(
    SECURE_SSL_REDIRECT=False,
    ALLOWED_HOSTS=["testserver"],
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
    },
    # Jobs run inline (eager) in tests — broker absent.
    CELERY_TASK_ALWAYS_EAGER=True,
    # Pin pipeline services OFF so tests never hit live APIs from ambient env.
    DEEPGRAM_API_KEY="",
    ELEVENLABS_API_KEY="",
    ELEVENLABS_VOICE_ID="",
    DEEPSEEK_API_KEY="",
)


@TEST_SETTINGS
class JobCreateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("maker", email="m@example.com", password="x")
        self.client = Client()
        self.client.force_login(self.user)

    def test_create_without_credits_fails_cleanly(self):
        response = self.client.post(reverse("jobs:create"), {"script": "Hello world"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Job.objects.count(), 0)
        self.assertEqual(CreditTransaction.objects.count(), 0)

    def test_create_with_credits_creates_job_and_spends(self):
        CreditAccount.grant(self.user, 5, CreditTransaction.Reason.PLAN_GRANT, "grant1")
        with patch("jobs.views.process_job.delay") as delay:
            response = self.client.post(
                reverse("jobs:create"),
                {"script": "Hello world. This is a test.", "footage": ""},
            )
        self.assertEqual(response.status_code, 302)
        job = Job.objects.get(user=self.user)
        self.assertEqual(job.credits_cost, 1)
        delay.assert_called_once_with(job.pk)
        account = CreditAccount.objects.get(user=self.user)
        self.assertEqual(account.balance, 4)

    def test_create_requires_login(self):
        response = Client().post(reverse("jobs:create"), {"script": "x"})
        self.assertEqual(response.status_code, 302)


@TEST_SETTINGS
class JobProgressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("p", email="p@example.com", password="x")
        self.other = User.objects.create_user("q", email="q@example.com", password="x")
        CreditAccount.grant(self.user, 3, CreditTransaction.Reason.PLAN_GRANT, "g")
        self.job = Job.objects.create(user=self.user, script="A script", credits_cost=1)

    def test_progress_requires_ownership(self):
        client = Client()
        client.force_login(self.other)
        response = client.get(reverse("jobs:progress", args=[self.job.pk]))
        self.assertEqual(response.status_code, 404)

    def test_progress_returns_json(self):
        client = Client()
        client.force_login(self.user)
        response = client.get(reverse("jobs:progress", args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "queued")


@TEST_SETTINGS
class PipelineValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("v", email="v@example.com", password="x")

    def _make_asset(self):
        from django.core.files.storage import default_storage

        asset = MediaAsset.objects.create(
            user=self.user,
            object_key=f"uploads/{self.user.pk}/test.mp4",
            content_type="video/mp4",
            size=100,
            status=MediaAsset.Status.VALIDATED,
        )
        default_storage.save(asset.object_key, ContentFile(b"dummy footage bytes"))
        return asset

    def test_empty_script_fails_and_should_refund(self):
        from . import pipeline

        job = Job.objects.create(user=self.user, script="   ", credits_cost=1)
        pipeline.run_pipeline(job)
        job.refresh_from_db()
        self.assertEqual(job.status, Job.Status.FAILED)
        self.assertTrue(pipeline.should_refund(job))

    def test_missing_footage_fails_and_should_refund(self):
        from . import pipeline

        job = Job.objects.create(user=self.user, script="A script", credits_cost=1)
        pipeline.run_pipeline(job)
        job.refresh_from_db()
        self.assertEqual(job.status, Job.Status.FAILED)
        self.assertTrue(pipeline.should_refund(job))

    def test_missing_elevenlabs_config_fails_cleanly_and_refunds(self):
        from . import pipeline

        asset = self._make_asset()
        job = Job.objects.create(
            user=self.user, script="A short script.", footage=asset, credits_cost=1
        )
        with self.assertRaises(RuntimeError):
            pipeline.run_pipeline(job)  # fails the job, then re-raises
        job.refresh_from_db()
        self.assertEqual(job.status, Job.Status.FAILED)
        self.assertIn("not configured", job.error)
        # No external API was consumed (Deepgram unconfigured, TTS never ran).
        self.assertTrue(pipeline.should_refund(job))

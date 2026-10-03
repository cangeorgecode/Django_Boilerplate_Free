import io
import json
import os
import shutil

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import MediaAsset

TEST_SETTINGS = override_settings(
    SECURE_SSL_REDIRECT=False,
    ALLOWED_HOSTS=["testserver"],
    # Pin R2 OFF: tests must exercise the local-storage path and never reach
    # the real bucket (ambient env / .env R2 keys would otherwise leak in).
    R2_ACCESS_KEY_ID="",
    R2_SECRET_ACCESS_KEY="",
    R2_BUCKET_NAME="",
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
    },
)


def _initiate(client, filename="clip.mp4", content_type="video/mp4", size=1024):
    return client.post(
        reverse("uploads:initiate"),
        data=json.dumps({"filename": filename, "content_type": content_type, "size": size}),
        content_type="application/json",
    )


@TEST_SETTINGS
class InitiateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("up", email="u@example.com", password="x")
        self.client = Client()
        self.client.force_login(self.user)

    def test_initiate_requires_login(self):
        response = _initiate(Client())
        self.assertEqual(response.status_code, 302)

    def test_initiate_rejects_bad_extension(self):
        response = _initiate(self.client, filename="evil.exe", content_type="application/x-msdownload")
        self.assertEqual(response.status_code, 400)

    def test_initiate_rejects_bad_content_type(self):
        response = _initiate(self.client, content_type="text/html")
        self.assertEqual(response.status_code, 400)

    def test_initiate_rejects_oversize(self):
        response = _initiate(self.client, size=10 * 1024**3)
        self.assertEqual(response.status_code, 400)

    def test_initiate_neutralizes_path_traversal_name(self):
        # The basename is stripped and the object key is a server UUID —
        # a traversal filename can never influence the storage key.
        response = _initiate(self.client, filename="../../etc/passwd.mp4")
        self.assertEqual(response.status_code, 200)
        asset = MediaAsset.objects.get(object_key=response.json()["object_key"])
        self.assertEqual(asset.original_name, "passwd.mp4")
        self.assertNotIn("..", asset.object_key)
        self.assertNotIn("etc", asset.object_key)

    def test_initiate_creates_pending_asset_direct_mode(self):
        response = _initiate(self.client)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["method"], "direct")
        asset = MediaAsset.objects.get(object_key=data["object_key"])
        self.assertEqual(asset.user, self.user)
        self.assertEqual(asset.status, MediaAsset.Status.PENDING)
        self.assertNotIn("..", asset.object_key)


@TEST_SETTINGS
class CompleteAndDownloadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("up2", email="u2@example.com", password="x")
        self.other = User.objects.create_user("other", email="o@example.com", password="x")
        self.client = Client()
        self.client.force_login(self.user)

    def _create_asset(self):
        response = _initiate(self.client)
        return response.json()["object_key"]

    def test_complete_accepts_real_file(self):
        object_key = self._create_asset()
        # A tiny valid media file: 0.5s of silence, generated at test time.
        import subprocess
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmp:
            media_path = os.path.join(tmp, "tiny.mp4")
            result = subprocess.run(
                ["ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                 "-t", "0.5", "-c:a", "aac", "-shortest", media_path],
                capture_output=True,
            )
            if result.returncode != 0:
                self.skipTest("ffmpeg unavailable")
            with open(media_path, "rb") as fh:
                content = fh.read()
        response = self.client.post(
            reverse("uploads:complete"),
            {"object_key": object_key, "file": SimpleUploadedFile("tiny.mp4", content, content_type="video/mp4")},
        )
        self.assertEqual(response.status_code, 200)
        asset = MediaAsset.objects.get(object_key=object_key)
        self.assertIn(asset.status, (MediaAsset.Status.VALIDATED, MediaAsset.Status.PENDING))

    def test_complete_rejects_garbage_file(self):
        object_key = self._create_asset()
        response = self.client.post(
            reverse("uploads:complete"),
            {"object_key": object_key, "file": SimpleUploadedFile("x.mp4", b"not media at all", content_type="video/mp4")},
        )
        self.assertEqual(response.status_code, 200)
        asset = MediaAsset.objects.get(object_key=object_key)
        self.assertEqual(asset.status, MediaAsset.Status.REJECTED)

    def test_download_requires_ownership(self):
        object_key = self._create_asset()
        other_client = Client()
        other_client.force_login(self.other)
        asset = MediaAsset.objects.get(object_key=object_key)
        response = other_client.get(reverse("uploads:download", args=[asset.pk]))
        self.assertEqual(response.status_code, 404)

    def test_delete_requires_ownership(self):
        object_key = self._create_asset()
        asset = MediaAsset.objects.get(object_key=object_key)
        other_client = Client()
        other_client.force_login(self.other)
        response = other_client.post(reverse("uploads:delete", args=[asset.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(MediaAsset.objects.filter(pk=asset.pk).exists())


@TEST_SETTINGS
@override_settings(MAX_STORAGE_BYTES_PER_USER=1500)
class QuotaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("quota", email="q@example.com", password="x")
        self.client = Client()
        self.client.force_login(self.user)

    def test_initiate_within_quota(self):
        response = _initiate(self.client, size=1000)
        self.assertEqual(response.status_code, 200)

    def test_initiate_blocks_over_quota(self):
        response = _initiate(self.client, size=2000)
        self.assertEqual(response.status_code, 400)
        self.assertIn("quota", response.json()["error"])

    def test_quota_counts_existing_assets(self):
        _initiate(self.client, size=1000)
        response = _initiate(self.client, size=600)  # 1600 total > 1500
        self.assertEqual(response.status_code, 400)


@TEST_SETTINGS
class UploadPageAndValidateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("pg", email="p@example.com", password="x")
        self.other = User.objects.create_user("oth", email="o2@example.com", password="x")
        self.client = Client()
        self.client.force_login(self.user)

    def test_upload_page_requires_login(self):
        response = Client().get(reverse("uploads:upload"))
        self.assertEqual(response.status_code, 302)

    def test_upload_page_renders(self):
        response = self.client.get(reverse("uploads:upload"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upload footage")

    def test_validate_requires_ownership(self):
        asset = MediaAsset.objects.create(
            user=self.other,
            object_key="uploads/99/abc.mp4",
            original_name="x.mp4",
            content_type="video/mp4",
            size=10,
        )
        response = self.client.post(reverse("uploads:validate", args=[asset.pk]))
        self.assertEqual(response.status_code, 404)

    def test_validate_rejects_garbage_file(self):
        object_key = _initiate(self.client).json()["object_key"]
        self.client.post(
            reverse("uploads:complete"),
            {"object_key": object_key,
             "file": SimpleUploadedFile("x.mp4", b"garbage bytes", content_type="video/mp4")},
        )
        asset = MediaAsset.objects.get(object_key=object_key)
        # The complete step may have validated already; exercise the endpoint
        # itself by resetting to pending.
        asset.status = MediaAsset.Status.PENDING
        asset.save(update_fields=["status"])
        response = self.client.post(reverse("uploads:validate", args=[asset.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], MediaAsset.Status.REJECTED)

    def test_validate_accepts_real_media(self):
        import subprocess
        import tempfile

        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("ffmpeg/ffprobe unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            media_path = os.path.join(tmp, "tiny.mp4")
            result = subprocess.run(
                ["ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                 "-t", "0.5", "-c:a", "aac", "-shortest", media_path],
                capture_output=True,
            )
            if result.returncode != 0:
                self.skipTest("ffmpeg unavailable")
            with open(media_path, "rb") as fh:
                content = fh.read()

        object_key = _initiate(self.client).json()["object_key"]
        self.client.post(
            reverse("uploads:complete"),
            {"object_key": object_key,
             "file": SimpleUploadedFile("tiny.mp4", content, content_type="video/mp4")},
        )
        asset = MediaAsset.objects.get(object_key=object_key)
        asset.status = MediaAsset.Status.PENDING
        asset.save(update_fields=["status"])
        response = self.client.post(reverse("uploads:validate", args=[asset.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], MediaAsset.Status.VALIDATED)

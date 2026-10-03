"""Storage plumbing: R2 (S3-compatible) presigned URLs + local-disk fallback.

Everything is keyed off whether R2 credentials exist, so the app runs fully
on local FileSystemStorage in dev and flips to R2 the moment the env vars
are set — no code changes.
"""
import json
import os
import shutil
import subprocess
import tempfile

import boto3
from botocore.client import Config
from django.conf import settings
from django.core.files.storage import default_storage

from .constants import MAX_DURATION_SECONDS, PRESIGN_DOWNLOAD_TTL, PRESIGN_UPLOAD_TTL
from .models import MediaAsset

_client = None


def r2_enabled():
    return bool(
        settings.R2_ACCESS_KEY_ID
        and settings.R2_SECRET_ACCESS_KEY
        and settings.R2_BUCKET_NAME
    )


def get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL or None,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},  # R2 has no virtual-hosted buckets
            ),
        )
    return _client


def presign_put(object_key, content_type):
    """Scoped PUT: exact key, declared content type, short TTL."""
    return get_client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.R2_BUCKET_NAME,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=PRESIGN_UPLOAD_TTL,
        HttpMethod="PUT",
    )


def presign_get(object_key):
    return get_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.R2_BUCKET_NAME, "Key": object_key},
        ExpiresIn=PRESIGN_DOWNLOAD_TTL,
    )


def head_object(object_key):
    """Return object metadata (ContentLength, ContentType) or None."""
    try:
        return get_client().head_object(
            Bucket=settings.R2_BUCKET_NAME, Key=object_key
        )
    except Exception:
        return None


def delete_object(object_key):
    try:
        get_client().delete_object(
            Bucket=settings.R2_BUCKET_NAME, Key=object_key
        )
        return True
    except Exception:
        return False


def download_to_file(object_key, destination_path):
    get_client().download_file(
        settings.R2_BUCKET_NAME, object_key, destination_path
    )


def ffprobe_available():
    return shutil.which("ffprobe") is not None


def probe_media(path):
    """Run ffprobe on untrusted media. Returns (ok, reason, duration_seconds)."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", path],
            capture_output=True, text=True, timeout=60,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False, "ffprobe timed out or is unavailable", None
    if result.returncode != 0:
        return False, "not a readable media file", None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False, "not a readable media file", None

    streams = data.get("streams") or []
    has_av = any(s.get("codec_type") in ("audio", "video") for s in streams)
    if not has_av:
        return False, "no audio or video stream found", None

    try:
        duration = float(data.get("format", {}).get("duration", 0))
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0:
        return False, "zero-duration media", None
    if duration > MAX_DURATION_SECONDS:
        return False, f"too long (>{MAX_DURATION_SECONDS}s)", duration
    return True, "", duration


def user_usage_bytes(user, exclude_asset=None):
    """Total bytes of a user's live assets (pending + validated).

    REJECTED assets are excluded: rejection reclaims the bytes from storage,
    so they no longer count against the quota. `exclude_asset` lets the
    complete step re-check quota against actual (not declared) sizes.
    """
    from django.db.models import Sum

    qs = MediaAsset.objects.filter(
        user=user, status__in=[MediaAsset.Status.PENDING, MediaAsset.Status.VALIDATED]
    )
    if exclude_asset is not None:
        qs = qs.exclude(pk=exclude_asset.pk)
    return qs.aggregate(total=Sum("size"))["total"] or 0


def quota_remaining_bytes(user):
    return max(0, settings.MAX_STORAGE_BYTES_PER_USER - user_usage_bytes(user))


def _delete_bytes(asset):
    """Remove an asset's bytes from storage (R2 or local) — used on rejection
    so quota is reclaimed and garbage never lingers."""
    try:
        if r2_enabled():
            delete_object(asset.object_key)
        else:
            default_storage.delete(asset.object_key)
    except Exception:
        pass


def validate_asset_media(asset):
    """Probe an asset's bytes and set status accordingly. For R2-backed
    assets the bytes are downloaded to scratch first; local files are probed
    in place. Returns the asset."""
    local_path = None
    try:
        if r2_enabled():
            local_path = tempfile.mktemp(suffix=".media")
            download_to_file(asset.object_key, local_path)
        else:
            local_path = default_storage.path(asset.object_key)
        ok, reason, duration = probe_media(local_path)
    except Exception as exc:
        ok, reason, duration = False, f"storage error: {exc}", None
    finally:
        if r2_enabled() and local_path and os.path.exists(local_path):
            try:
                os.unlink(local_path)
            except OSError:
                pass

    if ok:
        asset.status = asset.Status.VALIDATED
        asset.duration_seconds = duration
        asset.reject_reason = ""
    else:
        asset.status = asset.Status.REJECTED
        asset.reject_reason = reason[:255]
        _delete_bytes(asset)  # garbage never lingers; quota is reclaimed
    asset.save(update_fields=["status", "duration_seconds", "reject_reason"])
    return asset

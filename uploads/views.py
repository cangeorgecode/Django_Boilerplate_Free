import json
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .constants import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_BYTES,
)
from .models import MediaAsset, generate_object_key
from . import services


def _sanitize_filename(filename):
    """Keep only the basename, stripped of anything path-like."""
    name = os.path.basename(filename or "").strip()
    if name in (".", ".."):
        return ""
    return name[:255]


@login_required
@require_POST
def initiate(request):
    """Step 1: validate declared metadata, create the asset row, and hand back
    either a scoped presigned PUT URL (R2) or a direct-upload flag (local)."""
    try:
        data = json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "invalid json"}, status=400)

    filename = _sanitize_filename(data.get("filename", ""))
    content_type = (data.get("content_type") or "").lower()
    extension = os.path.splitext(filename)[1].lower() if filename else ""
    try:
        size = int(data.get("size", 0))
    except (TypeError, ValueError):
        return JsonResponse({"error": "invalid size"}, status=400)

    if extension not in ALLOWED_EXTENSIONS:
        return JsonResponse({"error": "file type not allowed"}, status=400)
    if content_type not in ALLOWED_CONTENT_TYPES:
        return JsonResponse({"error": "content type not allowed"}, status=400)
    if size <= 0 or size > MAX_UPLOAD_BYTES:
        return JsonResponse({"error": "file size not allowed"}, status=400)
    if services.user_usage_bytes(request.user) + size > settings.MAX_STORAGE_BYTES_PER_USER:
        return JsonResponse({"error": "storage quota exceeded"}, status=400)

    object_key = generate_object_key(request.user.pk, extension)
    asset = MediaAsset.objects.create(
        user=request.user,
        object_key=object_key,
        original_name=filename,
        content_type=content_type,
        size=size,
    )

    if services.r2_enabled():
        upload_url = services.presign_put(object_key, content_type)
        return JsonResponse({"method": "presign", "object_key": object_key, "upload_url": upload_url})
    return JsonResponse({"method": "direct", "object_key": object_key,
                         "upload_path": "/uploads/complete/"}, status=200)


@login_required
@require_POST
def complete(request):
    """Step 2: confirm the upload actually happened and is what was declared.
    Ownership is re-checked against the object key we generated."""
    object_key = (request.POST.get("object_key") or "").strip()
    if not object_key:
        return JsonResponse({"error": "missing object key"}, status=400)

    asset = get_object_or_404(MediaAsset, object_key=object_key, user=request.user)
    if asset.status != MediaAsset.Status.PENDING:
        return JsonResponse({"error": "upload already completed"}, status=400)

    if services.r2_enabled():
        head = services.head_object(object_key)
        if head is None:
            return JsonResponse({"error": "upload not found"}, status=400)
        actual_size = int(head.get("ContentLength") or 0)
        if actual_size > MAX_UPLOAD_BYTES:
            asset.status = MediaAsset.Status.REJECTED
            asset.reject_reason = "file too large"
            asset.save(update_fields=["status", "reject_reason"])
            return JsonResponse({"error": "file too large"}, status=400)
        # Re-check quota against the ACTUAL size (the declare step used the
        # client's claim), excluding this asset's own pending row.
        if services.user_usage_bytes(request.user, exclude_asset=asset) + actual_size > settings.MAX_STORAGE_BYTES_PER_USER:
            asset.status = MediaAsset.Status.REJECTED
            asset.reject_reason = "storage quota exceeded"
            asset.save(update_fields=["status", "reject_reason"])
            services._delete_bytes(asset)
            return JsonResponse({"error": "storage quota exceeded"}, status=400)
        asset.size = actual_size
        asset.save(update_fields=["size"])
        # Validation (ffprobe) happens in the background worker/command.
        return JsonResponse({"status": asset.status, "asset_id": asset.pk})

    # Local dev path: the browser uploads the file to us directly.
    uploaded = request.FILES.get("file")
    if uploaded is None:
        return JsonResponse({"error": "missing file"}, status=400)
    if uploaded.size > MAX_UPLOAD_BYTES:
        return JsonResponse({"error": "file too large"}, status=400)
    # Quota re-check against the actual size.
    if services.user_usage_bytes(request.user, exclude_asset=asset) + uploaded.size > settings.MAX_STORAGE_BYTES_PER_USER:
        asset.status = MediaAsset.Status.REJECTED
        asset.reject_reason = "storage quota exceeded"
        asset.save(update_fields=["status", "reject_reason"])
        return JsonResponse({"error": "storage quota exceeded"}, status=400)

    default_storage.save(object_key, uploaded)  # storage.save creates parent dirs
    asset.size = uploaded.size
    asset.save(update_fields=["size"])

    # Local files are cheap to validate synchronously.
    if services.ffprobe_available():
        asset = services.validate_asset_media(asset)
    return JsonResponse({"status": asset.status, "asset_id": asset.pk})


@login_required
@require_GET
def download(request, asset_id):
    asset = get_object_or_404(MediaAsset, pk=asset_id, user=request.user)
    if asset.status == MediaAsset.Status.REJECTED:
        return JsonResponse({"error": "file was rejected"}, status=400)

    if services.r2_enabled():
        return redirect(services.presign_get(asset.object_key))

    path = default_storage.path(asset.object_key)
    response = FileResponse(open(path, "rb"), content_type=asset.content_type or "application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{asset.display_name}"'
    return response


@login_required
@require_POST
def delete(request, asset_id):
    asset = get_object_or_404(MediaAsset, pk=asset_id, user=request.user)
    if services.r2_enabled():
        services.delete_object(asset.object_key)
    else:
        default_storage.delete(asset.object_key)
    asset.delete()
    return JsonResponse({"deleted": True})


@login_required
@require_GET
def my_assets(request):
    assets = request.user.media_assets.order_by("-created_at")[:50]
    return JsonResponse({
        "assets": [
            {
                "id": a.pk,
                "name": a.display_name,
                "status": a.status,
                "size": a.size,
                "duration_seconds": a.duration_seconds,
                "created_at": a.created_at.isoformat(),
            }
            for a in assets
        ]
    })


@login_required
@ensure_csrf_cookie
def upload_page(request):
    """The upload UI: a file picker that drives the initiate -> PUT/POST ->
    complete -> validate flow, plus the user's asset library."""
    assets = request.user.media_assets.order_by("-created_at")[:50]
    return render(request, "uploads/upload.html", {
        "assets": assets,
        "quota_bytes": settings.MAX_STORAGE_BYTES_PER_USER,
        "used_bytes": services.user_usage_bytes(request.user),
        "remaining_bytes": services.quota_remaining_bytes(request.user),
        "max_upload_bytes": MAX_UPLOAD_BYTES,
    })


@login_required
@require_POST
def validate(request, asset_id):
    """Run ffprobe validation on a pending asset (works for R2 and local
    storage). The upload page calls this right after `complete`."""
    asset = get_object_or_404(MediaAsset, pk=asset_id, user=request.user)
    if asset.status == MediaAsset.Status.VALIDATED:
        return JsonResponse({"status": asset.status, "asset_id": asset.pk})
    if asset.status != MediaAsset.Status.PENDING:
        return JsonResponse({"error": "asset cannot be validated"}, status=400)
    asset = services.validate_asset_media(asset)
    return JsonResponse({
        "status": asset.status,
        "asset_id": asset.pk,
        "reject_reason": asset.reject_reason,
    })

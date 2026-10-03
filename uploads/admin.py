from django.contrib import admin

from .models import MediaAsset


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "status", "size", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email", "user__username", "object_key", "original_name")
    readonly_fields = ("object_key", "size", "status", "reject_reason", "duration_seconds", "created_at")

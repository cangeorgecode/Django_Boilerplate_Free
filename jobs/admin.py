from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "progress", "credits_cost", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email", "user__username")
    readonly_fields = ("cost_breakdown", "logs", "created_at", "updated_at")

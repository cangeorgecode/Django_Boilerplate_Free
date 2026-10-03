from django.contrib import admin

from .models import CreditAccount, CreditTransaction, PaymentEvent, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "tier", "status", "current_period_end", "updated_at")
    list_filter = ("provider", "status", "tier")
    search_fields = ("user__email", "user__username", "provider_subscription_id")
    readonly_fields = ("provider_subscription_id", "created_at", "updated_at")


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_id", "event_type", "processed", "created_at")
    list_filter = ("provider", "processed")
    readonly_fields = ("provider", "event_id", "event_type", "payload", "processed", "created_at")


@admin.register(CreditAccount)
class CreditAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "updated_at")
    search_fields = ("user__email", "user__username")
    readonly_fields = ("balance",)


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ("account", "amount", "reason", "reference", "created_at")
    list_filter = ("reason",)
    readonly_fields = ("account", "amount", "reason", "reference", "created_at")

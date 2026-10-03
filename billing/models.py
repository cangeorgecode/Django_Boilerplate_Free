from django.contrib.auth.models import User
from django.db import models, transaction


class Subscription(models.Model):
    """A user's recurring plan from either gateway."""

    class Provider(models.TextChoices):
        LEMON_SQUEEZY = "lemonsqueezy"
        STRIPE = "stripe"

    class Status(models.TextChoices):
        TRIALING = "trialing"
        ACTIVE = "active"
        PAST_DUE = "past_due"
        CANCELED = "canceled"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    provider = models.CharField(max_length=20, choices=Provider.choices)
    provider_subscription_id = models.CharField(max_length=191, db_index=True)
    variant_id = models.CharField(max_length=191, blank=True, default="")
    tier = models.CharField(max_length=20, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    cancel_at_period_end = models.BooleanField(default=False)
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_subscription_id"],
                name="uniq_provider_subscription",
            )
        ]

    def __str__(self):
        return f"{self.user} — {self.provider}:{self.provider_subscription_id} ({self.status})"


class PaymentEvent(models.Model):
    """Audit log of every webhook received. The (provider, event_id) unique
    constraint is the replay/idempotency guard: a replayed event is dropped."""

    provider = models.CharField(max_length=20, choices=Subscription.Provider.choices)
    event_id = models.CharField(max_length=191)
    event_type = models.CharField(max_length=191, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "event_id"], name="uniq_provider_event")
        ]

    def __str__(self):
        return f"{self.provider}:{self.event_id} ({self.event_type})"


class CreditAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="credit_account")
    balance = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}: {self.balance} credits"

    @classmethod
    def get_or_create_for(cls, user):
        account, _ = cls.objects.get_or_create(user=user)
        return account

    @classmethod
    def grant(cls, user, amount, reason, reference):
        """Add credits atomically. Reference is an idempotency key (gateway
        event id) — a duplicate grant is a no-op."""
        if amount <= 0:
            raise ValueError("grant amount must be positive")
        with transaction.atomic():
            account, _ = cls.objects.get_or_create(user=user)
            account = cls.objects.select_for_update().get(pk=account.pk)
            if CreditTransaction.objects.filter(
                account=account, reason=reason, reference=reference
            ).exists():
                return account, False
            account.balance += amount
            account.save(update_fields=["balance", "updated_at"])
            tx = CreditTransaction.objects.create(
                account=account, amount=amount, reason=reason, reference=reference
            )
        return account, tx

    @classmethod
    def spend(cls, user, amount, reason, reference):
        """Deduct credits atomically. Raises ValueError when balance is
        insufficient — callers must handle it (never go negative)."""
        if amount <= 0:
            raise ValueError("spend amount must be positive")
        with transaction.atomic():
            account, _ = cls.objects.get_or_create(user=user)
            account = cls.objects.select_for_update().get(pk=account.pk)
            if CreditTransaction.objects.filter(
                account=account, reason=reason, reference=reference
            ).exists():
                return account, None
            if account.balance < amount:
                raise ValueError("insufficient credits")
            account.balance -= amount
            account.save(update_fields=["balance", "updated_at"])
            tx = CreditTransaction.objects.create(
                account=account, amount=-amount, reason=reason, reference=reference
            )
        return account, tx


class CreditTransaction(models.Model):
    """Immutable ledger entry: every credit movement has one row."""

    class Reason(models.TextChoices):
        PLAN_GRANT = "plan_grant"          # monthly plan credits
        TOPUP_PURCHASE = "topup_purchase"  # one-off top-up pack
        JOB_SPEND = "job_spend"            # a job consumed credits
        JOB_REFUND = "job_refund"          # refunded before execution
        ADMIN_ADJUST = "admin_adjust"      # manual admin adjustment

    account = models.ForeignKey(CreditAccount, on_delete=models.CASCADE, related_name="transactions")
    amount = models.IntegerField()  # positive = grant, negative = spend
    reason = models.CharField(max_length=30, choices=Reason.choices)
    reference = models.CharField(max_length=191, default="", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["account", "reason", "reference"]),
        ]

    def __str__(self):
        return f"{self.account.user} {self.amount:+d} ({self.reason})"

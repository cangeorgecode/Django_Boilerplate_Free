import hashlib
import hmac
import json

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import CreditAccount, CreditTransaction, PaymentEvent, Subscription
from .services import lemonsqueezy

TEST_SETTINGS = override_settings(
    SECURE_SSL_REDIRECT=False,
    ALLOWED_HOSTS=["testserver"],
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    },
)


@TEST_SETTINGS
class PricingPageTests(TestCase):
    def test_pricing_page_renders(self):
        response = Client().get(reverse("billing:pricing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Starter")
        self.assertContains(response, "Best Value")

    def test_checkout_requires_login(self):
        response = Client().post(reverse("billing:checkout", args=["starter"]))
        self.assertEqual(response.status_code, 302)

    def test_checkout_unconfigured_redirects_to_pricing(self):
        user = User.objects.create_user("buyer", email="b@example.com", password="x")
        client = Client()
        client.force_login(user)
        response = client.post(reverse("billing:checkout", args=["starter"]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("pricing", response.url)

    def test_checkout_unknown_tier_rejected(self):
        user = User.objects.create_user("buyer2", email="b2@example.com", password="x")
        client = Client()
        client.force_login(user)
        response = client.post(reverse("billing:checkout", args=["notatier"]))
        self.assertEqual(response.status_code, 400)


@TEST_SETTINGS
class WebhookRejectionTests(TestCase):
    def test_ls_webhook_rejects_bad_signature(self):
        response = Client().post(
            reverse("billing:lemonsqueezy_webhook"),
            data="{}",
            content_type="application/json",
            HTTP_X_SIGNATURE="deadbeef",
        )
        self.assertEqual(response.status_code, 400)

    def test_stripe_webhook_rejects_bad_signature(self):
        response = Client().post(
            reverse("billing:stripe_webhook"),
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=deadbeef",
        )
        self.assertEqual(response.status_code, 400)


@TEST_SETTINGS
class CreditLedgerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester", email="t@example.com", password="x")
        CreditAccount.get_or_create_for(self.user)

    def test_grant_and_spend(self):
        CreditAccount.grant(self.user, 10, CreditTransaction.Reason.PLAN_GRANT, "evt1")
        account = CreditAccount.objects.get(user=self.user)
        self.assertEqual(account.balance, 10)
        CreditAccount.spend(self.user, 3, CreditTransaction.Reason.JOB_SPEND, "job1")
        account.refresh_from_db()
        self.assertEqual(account.balance, 7)

    def test_grant_is_idempotent(self):
        CreditAccount.grant(self.user, 10, CreditTransaction.Reason.PLAN_GRANT, "evt1")
        _, second = CreditAccount.grant(self.user, 10, CreditTransaction.Reason.PLAN_GRANT, "evt1")
        self.assertFalse(second)
        self.assertEqual(CreditAccount.objects.get(user=self.user).balance, 10)

    def test_spend_insufficient_raises(self):
        with self.assertRaises(ValueError):
            CreditAccount.spend(self.user, 5, CreditTransaction.Reason.JOB_SPEND, "job1")


@TEST_SETTINGS
class LemonSqueezyWebhookTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("webuser", email="w@example.com", password="x")

    def _post_signed(self, body):
        payload = json.dumps(body).encode()
        signature = hmac.new(b"", payload, hashlib.sha256).hexdigest()  # empty secret in tests
        return Client().post(
            reverse("billing:lemonsqueezy_webhook"),
            data=payload,
            content_type="application/json",
            HTTP_X_SIGNATURE=signature,
        )

    def _subscription_body(self, event_name, subscription_id="sub-1", status="active"):
        return {
            "meta": {
                "event_name": event_name,
                "custom_data": {"user_id": str(self.user.pk), "tier": "starter"},
                "uuid": f"uuid-{event_name}-{subscription_id}",
            },
            "data": {
                "id": subscription_id,
                "type": "subscriptions",
                "attributes": {
                    "status": status,
                    "ends_at": "2026-10-29T00:00:00Z",
                    "variant_id": "123",
                },
            },
        }

    def test_subscription_created_upserts(self):
        response = self._post_signed(self._subscription_body("subscription_created"))
        self.assertEqual(response.status_code, 200)
        subscription = Subscription.objects.get(
            provider="lemonsqueezy", provider_subscription_id="sub-1"
        )
        self.assertEqual(subscription.status, "active")
        self.assertEqual(subscription.tier, "starter")
        self.assertEqual(subscription.user, self.user)

    def test_replay_is_dropped(self):
        body = self._subscription_body("subscription_created")
        self.assertEqual(self._post_signed(body).status_code, 200)
        self.assertEqual(self._post_signed(body).status_code, 200)
        self.assertEqual(Subscription.objects.count(), 1)
        self.assertEqual(PaymentEvent.objects.count(), 1)

    def test_payment_success_grants_plan_credits_once(self):
        body = self._subscription_body("subscription_payment_success")
        self.assertEqual(self._post_signed(body).status_code, 200)
        self.assertEqual(CreditAccount.objects.get(user=self.user).balance, 10)
        self.assertEqual(self._post_signed(body).status_code, 200)  # replay
        self.assertEqual(CreditAccount.objects.get(user=self.user).balance, 10)

    def test_cancelled_maps_status(self):
        response = self._post_signed(self._subscription_body("subscription_cancelled", status="cancelled"))
        self.assertEqual(response.status_code, 200)
        subscription = Subscription.objects.get(provider_subscription_id="sub-1")
        self.assertEqual(subscription.status, "canceled")


@TEST_SETTINGS
class CreditGrantOnTierResolutionTests(TestCase):
    def test_tier_of_variant_matches_env_configuration(self):
        from unittest.mock import patch

        from . import tiers

        with patch("billing.tiers.ls_variant_id", side_effect=lambda slug: {"starter": "v1"}.get(slug, "")):
            self.assertEqual(tiers.tier_of_variant("v1"), "starter")
            self.assertEqual(tiers.tier_of_variant("nope"), "")

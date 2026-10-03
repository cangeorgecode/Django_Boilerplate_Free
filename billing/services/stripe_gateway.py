"""Stripe gateway — secondary to Lemon Squeezy. Same contract as the LS
service so the shared billing module can treat them interchangeably."""
import logging

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

STATUS_MAP = {
    "trialing": "trialing",
    "active": "active",
    "past_due": "past_due",
    "unpaid": "past_due",
    "paused": "past_due",
    "canceled": "canceled",
    "incomplete_expired": "canceled",
}


def verify_signature(payload: bytes, sig_header: str):
    """Returns the verified event or raises stripe.error.SignatureVerificationError."""
    return stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )


def create_checkout(*, email, user_id, tier_slug, price_id, success_url, cancel_url):
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=email,
        line_items=[{"price": price_id, "quantity": 1}],
        metadata={"user_id": str(user_id), "tier": tier_slug},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


def create_payment(*, email, user_id, pack_slug, price_id, success_url, cancel_url):
    """One-off payment (top-up credit pack)."""
    session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=email,
        line_items=[{"price": price_id, "quantity": 1}],
        metadata={"user_id": str(user_id), "pack": pack_slug},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url

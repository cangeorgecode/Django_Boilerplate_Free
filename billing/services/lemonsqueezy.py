"""Lemon Squeezy v1 API client (Merchant of Record). No SDK — plain requests
per the proven recipe in the django-saas-boilerplate skill reference."""
import hashlib
import hmac
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.lemonsqueezy.com/v1"

# LS subscription status -> local Subscription.Status
STATUS_MAP = {
    "on_trial": "trialing",
    "active": "active",
    "past_due": "past_due",
    "unpaid": "past_due",
    "paused": "past_due",
    "cancelled": "canceled",
    "expired": "canceled",
}

SUBSCRIPTION_EVENTS = {
    "subscription_created",
    "subscription_updated",
    "subscription_resumed",
    "subscription_cancelled",
    "subscription_expired",
    "subscription_paused",
    "subscription_unpaused",
    "subscription_payment_success",
    "subscription_payment_failed",
}


def _headers():
    return {
        "Authorization": f"Bearer {settings.LEMONSQUEEZY_API_KEY}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }


def verify_signature(payload: bytes, signature: str) -> bool:
    """HMAC-SHA256 of the RAW request body. Verify BEFORE parsing JSON."""
    secret = (settings.LEMONSQUEEZY_WEBHOOK_SECRET or "").encode()
    digest = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature or "")


def parse_event(body: dict):
    """Return (event_name, event_id, custom_data, attributes, data) from a webhook body."""
    meta = body.get("meta") or {}
    data = body.get("data") or {}
    attributes = data.get("attributes") or {}
    custom = meta.get("custom_data") or {}
    event_name = meta.get("event_name", "")
    event_id = meta.get("uuid") or str(data.get("id", ""))
    return event_name, event_id, custom, attributes, data


def create_checkout(*, email, user_id, tier_slug, variant_id, redirect_url):
    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": email,
                    "custom": {"user_id": str(user_id), "tier": tier_slug},
                },
                "product_options": {"redirect_url": redirect_url},
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": str(settings.LEMONSQUEEZY_STORE_ID)}},
                "variant": {"data": {"type": "variants", "id": str(variant_id)}},
            },
        }
    }
    response = requests.post(f"{BASE_URL}/checkouts", json=payload, headers=_headers(), timeout=20)
    response.raise_for_status()
    return response.json()["data"]["attributes"]["url"]


def get_subscription(subscription_id):
    response = requests.get(
        f"{BASE_URL}/subscriptions/{subscription_id}", headers=_headers(), timeout=20
    )
    response.raise_for_status()
    return response.json()


def set_cancel(subscription_id, cancelled):
    payload = {
        "data": {
            "type": "subscriptions",
            "id": str(subscription_id),
            "attributes": {"cancelled": bool(cancelled)},
        }
    }
    response = requests.patch(
        f"{BASE_URL}/subscriptions/{subscription_id}", json=payload, headers=_headers(), timeout=20
    )
    response.raise_for_status()
    return response.json()


def portal_url(subscription_id):
    data = get_subscription(subscription_id)
    return data["data"]["attributes"]["urls"].get("customer_portal")

"""Single source of truth for plans, tiers, and gateway configuration.

Pricing NEVER comes from the client: checkouts are created server-side from
these definitions, and every webhook is re-validated against them before any
credits or access are granted.
"""
import os

TIERS = [
    {
        "slug": "starter",
        "name": "Starter",
        "monthly_usd": 19,
        "credits": 10,
        "badge": "",
        "blurb": "For trying things out",
    },
    {
        "slug": "growth",
        "name": "Growth",
        "monthly_usd": 45,
        "credits": 20,
        "badge": "",
        "blurb": "Regular creators",
    },
    {
        "slug": "scale",
        "name": "Scale",
        "monthly_usd": 49,
        "credits": 30,
        "badge": "Best Value",
        "blurb": "Serious output",
    },
]

TOPUP_PACKS = [
    {"slug": "topup_5", "credits": 5, "price_usd": 9, "name": "5 credits"},
]

TIER_BY_SLUG = {t["slug"]: t for t in TIERS}
TIER_SLUGS = list(TIER_BY_SLUG.keys())
TOPUP_BY_SLUG = {t["slug"]: t for t in TOPUP_PACKS}


def _env_upper(*parts):
    return "_".join(p.upper() for p in parts)


def ls_variant_id(tier_slug):
    return os.getenv(_env_upper("LEMONSQUEEZY", "VARIANT", tier_slug), "")


def stripe_price_id(tier_slug):
    return os.getenv(_env_upper("STRIPE", "PRICE", tier_slug), "")


def lemonsqueezy_configured():
    return all(
        os.getenv(key)
        for key in (
            "LEMONSQUEEZY_API_KEY",
            "LEMONSQUEEZY_WEBHOOK_SECRET",
            "LEMONSQUEEZY_STORE_ID",
        )
    )


def stripe_configured():
    return all(os.getenv(key) for key in ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"))


def primary_provider():
    """Lemon Squeezy (Merchant of Record) first; Stripe as fallback."""
    if lemonsqueezy_configured():
        return "lemonsqueezy"
    if stripe_configured():
        return "stripe"
    return None


def tier_configured(tier_slug, provider=None):
    provider = provider or primary_provider()
    if provider == "lemonsqueezy":
        return bool(ls_variant_id(tier_slug))
    if provider == "stripe":
        return bool(stripe_price_id(tier_slug))
    return False


def tier_of_variant(variant_id):
    """Reverse map a gateway variant id back to a tier slug (server-side truth)."""
    variant_id = str(variant_id or "")
    if not variant_id:
        return ""
    for tier in TIERS:
        if ls_variant_id(tier["slug"]) == variant_id:
            return tier["slug"]
    return ""

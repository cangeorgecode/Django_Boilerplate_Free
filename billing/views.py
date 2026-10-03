import json
import logging
from datetime import datetime

import stripe
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import tiers
from .models import CreditAccount, CreditTransaction, PaymentEvent, Subscription
from .services import lemonsqueezy, stripe_gateway

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

def pricing(request):
    provider = tiers.primary_provider()
    tier_cards = []
    for tier in tiers.TIERS:
        tier_cards.append(
            {
                **tier,
                "per_credit": round(tier["monthly_usd"] / tier["credits"], 2),
                "configured": tiers.tier_configured(tier["slug"], provider),
            }
        )
    return render(
        request,
        "billing/pricing.html",
        {
            "tier_cards": tier_cards,
            "provider": provider,
            "billing_configured": provider is not None,
        },
    )


@login_required
@require_POST
def checkout(request, tier_slug):
    if tier_slug not in tiers.TIER_BY_SLUG:
        return HttpResponseBadRequest("Unknown plan.")
    provider = tiers.primary_provider()
    if not provider:
        messages.error(request, "Billing is not configured yet. Please try again later.")
        return redirect("billing:pricing")
    if not tiers.tier_configured(tier_slug, provider):
        messages.error(request, "This plan is not available yet. Please try again later.")
        return redirect("billing:pricing")

    tier = tiers.TIER_BY_SLUG[tier_slug]
    success_url = request.build_absolute_uri(reverse("billing:checkout_success"))
    cancel_url = request.build_absolute_uri(reverse("billing:pricing"))

    try:
        if provider == "lemonsqueezy":
            checkout_url = lemonsqueezy.create_checkout(
                email=request.user.email or "",
                user_id=request.user.pk,
                tier_slug=tier_slug,
                variant_id=tiers.ls_variant_id(tier_slug),
                redirect_url=success_url,
            )
        else:
            checkout_url = stripe_gateway.create_checkout(
                email=request.user.email or "",
                user_id=request.user.pk,
                tier_slug=tier_slug,
                price_id=tiers.stripe_price_id(tier_slug),
                success_url=success_url,
                cancel_url=cancel_url,
            )
    except Exception:
        logger.exception("checkout creation failed for tier=%s user=%s", tier_slug, request.user.pk)
        messages.error(request, "Could not start checkout. Please try again later.")
        return redirect("billing:pricing")

    return redirect(checkout_url)


def checkout_success(request):
    return render(request, "billing/checkout_success.html")


def checkout_cancel(request):
    return render(request, "billing/checkout_cancel.html")


@login_required
def manage(request):
    subscriptions = request.user.subscriptions.order_by("-created_at")
    account = CreditAccount.get_or_create_for(request.user)
    context = {
        "subscriptions": subscriptions,
        "active_subscription": subscriptions.filter(status__in=["trialing", "active", "past_due"]).first(),
        "credit_balance": account.balance,
        "transactions": account.transactions.order_by("-created_at")[:20],
        "topup_packs": tiers.TOPUP_PACKS,
        "billing_configured": tiers.primary_provider() is not None,
        "ls_portal_available": subscriptions.filter(
            provider="lemonsqueezy", status__in=["trialing", "active", "past_due"]
        ).exists(),
    }
    return render(request, "billing/manage.html", context)


@login_required
@require_POST
def manage_cancel(request, subscription_id):
    subscription = get_object_or_404(
        Subscription, id=subscription_id, user=request.user
    )
    try:
        if subscription.provider == Subscription.Provider.LEMON_SQUEEZY:
            data = lemonsqueezy.set_cancel(subscription.provider_subscription_id, cancelled=True)
            attributes = data["data"]["attributes"]
            subscription.cancel_at_period_end = bool(attributes.get("cancelled"))
            subscription.status = lemonsqueezy.STATUS_MAP.get(attributes.get("status", ""), subscription.status)
        else:
            stripe.Subscription.modify(
                subscription.provider_subscription_id, cancel_at_period_end=True
            )
            subscription.cancel_at_period_end = True
        subscription.save(update_fields=["cancel_at_period_end", "status", "updated_at"])
        messages.success(request, "Your subscription will be cancelled at the end of the billing period.")
    except Exception:
        logger.exception("cancel failed for subscription=%s", subscription.pk)
        messages.error(request, "Could not cancel the subscription. Please try again later.")
    return redirect("billing:manage")


@login_required
@require_POST
def manage_resume(request, subscription_id):
    subscription = get_object_or_404(
        Subscription, id=subscription_id, user=request.user
    )
    try:
        if subscription.provider == Subscription.Provider.LEMON_SQUEEZY:
            data = lemonsqueezy.set_cancel(subscription.provider_subscription_id, cancelled=False)
            attributes = data["data"]["attributes"]
            subscription.cancel_at_period_end = bool(attributes.get("cancelled"))
            subscription.status = lemonsqueezy.STATUS_MAP.get(attributes.get("status", ""), subscription.status)
        else:
            stripe.Subscription.modify(
                subscription.provider_subscription_id, cancel_at_period_end=False
            )
            subscription.cancel_at_period_end = False
        subscription.save(update_fields=["cancel_at_period_end", "status", "updated_at"])
        messages.success(request, "Your subscription is active again.")
    except Exception:
        logger.exception("resume failed for subscription=%s", subscription.pk)
        messages.error(request, "Could not resume the subscription. Please try again later.")
    return redirect("billing:manage")


@login_required
@require_POST
def topup(request, pack_slug):
    if pack_slug not in tiers.TOPUP_BY_SLUG:
        return HttpResponseBadRequest("Unknown pack.")
    provider = tiers.primary_provider()
    if not provider:
        messages.error(request, "Billing is not configured yet. Please try again later.")
        return redirect("billing:manage")

    pack = tiers.TOPUP_BY_SLUG[pack_slug]
    success_url = request.build_absolute_uri(reverse("billing:checkout_success"))
    cancel_url = request.build_absolute_uri(reverse("billing:manage"))

    try:
        if provider == "lemonsqueezy":
            variant_id = tiers.ls_variant_id(pack_slug)
            if not variant_id:
                raise ValueError("top-up variant not configured")
            checkout_url = lemonsqueezy.create_checkout(
                email=request.user.email or "",
                user_id=request.user.pk,
                tier_slug=pack_slug,
                variant_id=variant_id,
                redirect_url=success_url,
            )
        else:
            price_id = tiers.stripe_price_id(pack_slug)
            if not price_id:
                raise ValueError("top-up price not configured")
            checkout_url = stripe_gateway.create_payment(
                email=request.user.email or "",
                user_id=request.user.pk,
                pack_slug=pack_slug,
                price_id=price_id,
                success_url=success_url,
                cancel_url=cancel_url,
            )
    except Exception:
        logger.exception("top-up checkout failed pack=%s user=%s", pack_slug, request.user.pk)
        messages.error(request, "Could not start checkout. Please try again later.")
        return redirect("billing:manage")

    return redirect(checkout_url)


@login_required
def portal(request):
    subscription = (
        request.user.subscriptions.filter(
            provider="lemonsqueezy", status__in=["trialing", "active", "past_due"]
        )
        .order_by("-created_at")
        .first()
    )
    if not subscription:
        messages.error(request, "No active subscription to manage.")
        return redirect("billing:manage")
    try:
        url = lemonsqueezy.portal_url(subscription.provider_subscription_id)
        if not url:
            raise ValueError("no portal url")
        return redirect(url)
    except Exception:
        logger.exception("portal lookup failed for subscription=%s", subscription.pk)
        messages.error(request, "Could not open the billing portal. Please try again later.")
        return redirect("billing:manage")


# --------------------------------------------------------------------------
# Webhooks — signature verified BEFORE parsing; idempotent via PaymentEvent
# --------------------------------------------------------------------------

@csrf_exempt
def lemonsqueezy_webhook(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    if not lemonsqueezy.verify_signature(request.body, request.headers.get("X-Signature", "")):
        logger.warning("LS webhook rejected: bad signature")
        return HttpResponse("invalid signature", status=400)
    try:
        body = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return HttpResponse("invalid json", status=400)

    event_name, event_id, custom, attributes, data = lemonsqueezy.parse_event(body)
    if not event_id:
        return HttpResponse(status=400)

    event, created = PaymentEvent.objects.get_or_create(
        provider=Subscription.Provider.LEMON_SQUEEZY,
        event_id=event_id,
        defaults={"event_type": event_name, "payload": body},
    )
    if not created:
        # Replay (or the same event re-delivered) — never process twice.
        return HttpResponse(status=200)

    try:
        _handle_lemonsqueezy_event(event_name, custom, attributes, data)
    except Exception:
        logger.exception("LS event handling failed event_id=%s", event_id)
        # Leave processed=False so a redelivery retries it.
        return HttpResponse(status=500)

    event.processed = True
    event.save(update_fields=["processed"])
    return HttpResponse(status=200)


def _handle_lemonsqueezy_event(event_name, custom, attributes, data=None):
    data = data or {}
    if event_name in lemonsqueezy.SUBSCRIPTION_EVENTS:
        _upsert_subscription(
            provider=Subscription.Provider.LEMON_SQUEEZY,
            user_id=custom.get("user_id"),
            provider_subscription_id=attributes.get("id") or attributes.get("subscription_id") or data.get("id"),
            variant_id=attributes.get("variant_id"),
            tier=custom.get("tier") or tiers.tier_of_variant(attributes.get("variant_id")),
            status=lemonsqueezy.STATUS_MAP.get(attributes.get("status", ""), "active"),
            cancel_at_period_end=bool(attributes.get("cancelled")),
            ends_at=attributes.get("ends_at") or attributes.get("renews_at"),
        )
    if event_name in ("subscription_payment_success", "subscription_payment_recovered"):
        _grant_plan_credits(event_name, custom, attributes)
    elif event_name == "order_created":
        _handle_order_paid(event_name, custom, attributes)


@csrf_exempt
def stripe_webhook(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    try:
        event = stripe_gateway.verify_signature(request.body, request.headers.get("Stripe-Signature", ""))
    except (ValueError, stripe.error.SignatureVerificationError):
        logger.warning("Stripe webhook rejected: bad signature")
        return HttpResponse("invalid signature", status=400)

    stripe_event, created = PaymentEvent.objects.get_or_create(
        provider=Subscription.Provider.STRIPE,
        event_id=event["id"],
        defaults={"event_type": event["type"], "payload": event},
    )
    if not created:
        return HttpResponse(status=200)

    try:
        _handle_stripe_event(event)
    except Exception:
        logger.exception("Stripe event handling failed event_id=%s", event["id"])
        return HttpResponse(status=500)

    stripe_event.processed = True
    stripe_event.save(update_fields=["processed"])
    return HttpResponse(status=200)


def _handle_stripe_event(event):
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        metadata = data.get("metadata") or {}
        if data.get("mode") == "subscription":
            _upsert_subscription(
                provider=Subscription.Provider.STRIPE,
                user_id=metadata.get("user_id"),
                provider_subscription_id=data.get("subscription"),
                variant_id="",
                tier=metadata.get("tier", ""),
                status="active",
                cancel_at_period_end=False,
                ends_at=None,
            )
        elif data.get("mode") == "payment" and metadata.get("pack"):
            # One-off top-up pack — grant credits idempotently by session id.
            try:
                user = User.objects.get(pk=int(metadata.get("user_id")))
            except (TypeError, ValueError, User.DoesNotExist):
                user = None
            pack = tiers.TOPUP_BY_SLUG.get(metadata.get("pack"))
            if user and pack:
                CreditAccount.grant(
                    user,
                    pack["credits"],
                    CreditTransaction.Reason.TOPUP_PURCHASE,
                    f"stripe_session_{data.get('id')}",
                )
    elif event_type.startswith("customer.subscription."):
        metadata = data.get("metadata") or {}
        _upsert_subscription(
            provider=Subscription.Provider.STRIPE,
            user_id=metadata.get("user_id"),
            provider_subscription_id=data.get("id"),
            variant_id="",
            tier=metadata.get("tier", ""),
            status=stripe_gateway.STATUS_MAP.get(data.get("status", ""), "active"),
            cancel_at_period_end=bool(data.get("cancel_at_period_end")),
            ends_at=None,
        )
    elif event_type == "invoice.paid":
        subscription = Subscription.objects.filter(
            provider=Subscription.Provider.STRIPE,
            provider_subscription_id=str(data.get("subscription") or ""),
        ).first()
        tier = tiers.TIER_BY_SLUG.get(subscription.tier) if subscription else None
        if subscription and tier:
            CreditAccount.grant(
                subscription.user,
                tier["credits"],
                CreditTransaction.Reason.PLAN_GRANT,
                f"stripe_invoice_{data.get('id')}",
            )


# --------------------------------------------------------------------------
# Shared subscription / credit logic (server-side truth)
# --------------------------------------------------------------------------

def _upsert_subscription(*, provider, user_id, provider_subscription_id, variant_id,
                         tier, status, cancel_at_period_end, ends_at):
    if not provider_subscription_id:
        return None
    with transaction.atomic():
        subscription = Subscription.objects.filter(
            provider=provider, provider_subscription_id=str(provider_subscription_id)
        ).first()
        if subscription is None:
            try:
                user = User.objects.get(pk=int(user_id)) if user_id else None
            except (TypeError, ValueError, User.DoesNotExist):
                logger.warning("subscription event without resolvable user_id=%r", user_id)
                return None
            subscription = Subscription(
                user=user, provider=provider,
                provider_subscription_id=str(provider_subscription_id),
            )
        subscription.variant_id = str(variant_id or "")
        subscription.tier = tier or ""
        subscription.status = status
        subscription.cancel_at_period_end = bool(cancel_at_period_end)
        if ends_at:
            try:
                subscription.current_period_end = datetime.fromisoformat(
                    str(ends_at).replace("Z", "+00:00")
                )
            except ValueError:
                pass
        subscription.save()
    return subscription


def _grant_plan_credits(reference, custom, attributes):
    """Grant the monthly plan credits exactly once per payment event."""
    user_id = custom.get("user_id") if isinstance(custom, dict) else None
    if not user_id:
        return
    try:
        user = User.objects.get(pk=int(user_id))
    except (TypeError, ValueError, User.DoesNotExist):
        return
    tier_slug = custom.get("tier") or ""
    tier = tiers.TIER_BY_SLUG.get(tier_slug)
    if not tier:
        return
    CreditAccount.grant(user, tier["credits"], CreditTransaction.Reason.PLAN_GRANT, str(reference))


def _handle_order_paid(reference, custom, attributes):
    """LS one-off orders (top-up packs). Credits are granted only when the
    order is actually paid — the webhook for that is order_created with
    status 'paid'."""
    status = attributes.get("status", "")
    if status not in ("paid",):
        return
    user_id = custom.get("user_id")
    if not user_id:
        return
    try:
        user = User.objects.get(pk=int(user_id))
    except (TypeError, ValueError, User.DoesNotExist):
        return
    variant_id = str(attributes.get("first_order_item", {}).get("variant_id") or "")
    pack = None
    for candidate in tiers.TOPUP_PACKS:
        if tiers.ls_variant_id(candidate["slug"]) == variant_id:
            pack = candidate
            break
    if not pack:
        logger.warning("order_created with unknown variant %s", variant_id)
        return
    CreditAccount.grant(user, pack["credits"], CreditTransaction.Reason.TOPUP_PURCHASE, str(reference))

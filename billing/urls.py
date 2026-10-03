from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("pricing/", views.pricing, name="pricing"),
    path("checkout/<slug:tier_slug>/", views.checkout, name="checkout"),
    path("checkout/success/", views.checkout_success, name="checkout_success"),
    path("checkout/cancel/", views.checkout_cancel, name="checkout_cancel"),
    path("webhooks/lemonsqueezy/", views.lemonsqueezy_webhook, name="lemonsqueezy_webhook"),
    path("webhooks/stripe/", views.stripe_webhook, name="stripe_webhook"),
    path("manage/", views.manage, name="manage"),
    path("topup/<slug:pack_slug>/", views.topup, name="topup"),
    path("manage/cancel/<int:subscription_id>/", views.manage_cancel, name="manage_cancel"),
    path("manage/resume/<int:subscription_id>/", views.manage_resume, name="manage_resume"),
    path("portal/", views.portal, name="portal"),
]

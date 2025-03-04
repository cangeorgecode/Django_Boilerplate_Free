from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('price/', views.pricing, name='pricing'),
    path('payment_successful/', views.payment_successful, name='payment_successful'),
    path('payment_cancelled/', views.payment_cancel, name='payment_cancelled'),
    path('stripe_webhook/', views.stripe_webhook, name='stripe_webhook'),
]
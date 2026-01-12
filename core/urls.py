from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('success/', views.success_view, name='success'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
]
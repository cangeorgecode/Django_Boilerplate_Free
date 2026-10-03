from django.urls import path, include
from . import views

urlpatterns = [
    path('', include('allauth.urls')),
    path('profile/', views.profile, name='profile'),
    path('profile/delete/confirm/', views.profile_delete_confirm, name='profile_delete_confirm'),
    path('profile/delete/', views.profile_delete, name='profile_delete'),
    path('admin/email/', views.admin_send_email, name='admin_send_email'),
]

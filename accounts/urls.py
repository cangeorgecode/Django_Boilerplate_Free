from django.urls import path, include
from . import views

urlpatterns = [
    path('', include('allauth.urls')),
    path('profile/', views.profile, name='profile'),
    path('check-username/', views.check_username, name='check_username'),
    path('profile/edit/form/', views.profile_edit_form, name='profile_edit_form'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/delete/confirm/', views.profile_delete_confirm, name='profile_delete_confirm'),
    path('profile/delete/', views.profile_delete, name='profile_delete'),
]
from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("create/", views.create, name="create"),
    path("", views.list_jobs, name="list"),
    path("<int:job_id>/", views.detail, name="detail"),
    path("<int:job_id>/progress/", views.progress, name="progress"),
]

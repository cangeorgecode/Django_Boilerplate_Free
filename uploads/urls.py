from django.urls import path

from . import views

app_name = "uploads"

urlpatterns = [
    path("", views.upload_page, name="upload"),
    path("initiate/", views.initiate, name="initiate"),
    path("complete/", views.complete, name="complete"),
    path("assets/", views.my_assets, name="my_assets"),
    path("assets/<int:asset_id>/validate/", views.validate, name="validate"),
    path("assets/<int:asset_id>/download/", views.download, name="download"),
    path("assets/<int:asset_id>/delete/", views.delete, name="delete"),
]

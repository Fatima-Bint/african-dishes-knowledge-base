from django.contrib import admin
from django.urls import include, path

from dishes import views


urlpatterns = [
    path("admin/exports/dishes.json", views.export_json, name="admin_export_json"),
    path("admin/exports/dishes.csv", views.export_csv, name="admin_export_csv"),
    path("admin/", admin.site.urls),
    path("", include("dishes.urls")),
]

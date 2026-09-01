from django.urls import path

from . import views


app_name = "dishes"

urlpatterns = [
    path("", views.catalogue, name="catalogue"),
    path("demo/", views.demo, name="demo"),
    path("dishes/<slug:slug>/", views.dish_detail, name="detail"),
    path("api/dishes/", views.api_dishes, name="api_dishes"),
    path("exports/dishes.json", views.export_json, name="export_json"),
    path("exports/dishes.csv", views.export_csv, name="export_csv"),
]

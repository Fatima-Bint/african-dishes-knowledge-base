import csv
import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import DishCategory, Location
from .services import public_dishes, serialize_dish


def _filters(request):
    return {
        "query": request.GET.get("q", "").strip(),
        "location": request.GET.get("location", "").strip(),
        "category": request.GET.get("category", "").strip(),
    }


def catalogue(request):
    filters = _filters(request)
    dishes = public_dishes(**filters)
    locations = Location.objects.filter(
        dish_associations__dish__publication_status="published",
        dish_associations__review_status__in=["reviewed", "corroborated"],
    ).distinct().order_by("name")
    categories = DishCategory.objects.filter(
        dishes__publication_status="published"
    ).distinct().order_by("name")

    return render(
        request,
        "dishes/catalogue.html",
        {
            "dishes": dishes,
            "locations": locations,
            "categories": categories,
            **filters,
        },
    )


def dish_detail(request, slug):
    dish = get_object_or_404(public_dishes(), slug=slug)
    return render(
        request,
        "dishes/detail.html",
        {"dish": dish, "record": serialize_dish(dish)},
    )


def api_dishes(request):
    records = [serialize_dish(dish) for dish in public_dishes(**_filters(request))]
    return JsonResponse({"count": len(records), "results": records})


def export_json(request):
    records = [serialize_dish(dish) for dish in public_dishes(**_filters(request))]
    response = HttpResponse(
        json.dumps(records, indent=2, ensure_ascii=False),
        content_type="application/json; charset=utf-8",
    )
    response["Content-Disposition"] = 'attachment; filename="ghana-dishes-pilot.json"'
    return response


def export_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="ghana-dishes-pilot.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "canonical_name",
            "alternative_names",
            "category",
            "locations",
            "review_status",
            "source_urls",
        ]
    )

    for dish in public_dishes(**_filters(request)):
        record = serialize_dish(dish)
        writer.writerow(
            [
                record["canonical_name"],
                " | ".join(item["name"] for item in record["alternative_names"]),
                record["category"] or "",
                " | ".join(item["name"] for item in record["locations"]),
                record["review_status"],
                " | ".join(
                    sorted(
                        {
                            item["source"]["url"]
                            for item in record["evidence"]
                            if item["source"]["url"]
                        }
                    )
                ),
            ]
        )
    return response

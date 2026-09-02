import csv
import json
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import CandidateRecord, DishCategory, Location, ReviewDecision
from .services import approve_candidate_as_new_dish, public_dishes, serialize_dish


YOUTUBE_VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


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


def demo(request):
    video_id = settings.DEMO_VIDEO_ID
    if not YOUTUBE_VIDEO_ID_PATTERN.fullmatch(video_id):
        video_id = ""
    return render(request, "dishes/demo.html", {"video_id": video_id})


def dish_detail(request, slug):
    dish = get_object_or_404(public_dishes(), slug=slug)
    return render(
        request,
        "dishes/detail.html",
        {
            "dish": dish,
            "record": serialize_dish(dish, include_evidence=request.user.is_staff),
        },
    )


def api_dishes(request):
    records = [
        serialize_dish(dish, include_evidence=request.user.is_staff)
        for dish in public_dishes(**_filters(request))
    ]
    return JsonResponse({"count": len(records), "results": records})


@staff_member_required
def export_json(request):
    records = [serialize_dish(dish) for dish in public_dishes(**_filters(request))]
    response = HttpResponse(
        json.dumps(records, indent=2, ensure_ascii=False),
        content_type="application/json; charset=utf-8",
    )
    response["Content-Disposition"] = 'attachment; filename="ghana-dishes-pilot.json"'
    return response


@staff_member_required
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
            "wikidata_id",
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
                record["wikidata_id"] or "",
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


def _candidate_value(payload, key):
    value = payload.get(key)
    if isinstance(value, dict):
        return value.get("value") or ""
    return value or ""


def _candidate_alternatives(payload):
    names = []
    for item in payload.get("alternative_names") or []:
        if isinstance(item, dict):
            value = item.get("name") or item.get("value")
        else:
            value = item
        if value:
            names.append(str(value).strip())
    return names


@staff_member_required
def curator_queue(request):
    candidates = (
        CandidateRecord.objects.exclude(
            processing_status=CandidateRecord.ProcessingStatus.DECIDED
        )
        .select_related("source")
        .prefetch_related("source__excerpts", "match_suggestions__proposed_dish")
        .order_by("-created_at")
    )
    return render(request, "dishes/curator_queue.html", {"candidates": candidates})


@staff_member_required
def curator_review(request, candidate_id):
    candidate = get_object_or_404(
        CandidateRecord.objects.select_related("source").prefetch_related(
            "source__excerpts", "match_suggestions__proposed_dish"
        ),
        id=candidate_id,
    )
    payload = candidate.extracted_payload or {}
    alternatives = _candidate_alternatives(payload)

    if request.method == "POST":
        action = request.POST.get("action")
        notes = request.POST.get("notes", "").strip()

        if action == "approve_new":
            corrected_payload = {
                "candidate_name": request.POST.get("candidate_name", "").strip(),
                "description": {
                    "value": request.POST.get("description", "").strip(),
                    "evidence": _candidate_value(payload, "description"),
                },
                "category": {
                    "value": request.POST.get("category", "").strip(),
                    "evidence": _candidate_value(payload, "category"),
                },
                "alternative_names": [
                    {"name": name.strip(), "language_code": "en"}
                    for name in request.POST.get("alternative_names", "").split(",")
                    if name.strip()
                ],
            }
            try:
                dish = approve_candidate_as_new_dish(
                    candidate,
                    request.user,
                    corrected_payload=corrected_payload,
                    notes=notes,
                )
            except ValueError as error:
                messages.error(request, str(error))
            else:
                messages.success(request, f"{dish.canonical_name} is now published.")
                return redirect("dishes:detail", slug=dish.slug)

        elif action in {"needs_evidence", "reject"}:
            review_action = (
                ReviewDecision.Action.NEEDS_EVIDENCE
                if action == "needs_evidence"
                else ReviewDecision.Action.REJECT
            )
            ReviewDecision.objects.create(
                candidate=candidate,
                reviewer=request.user,
                action=review_action,
                notes=notes,
                corrected_payload=payload,
            )
            candidate.processing_status = (
                CandidateRecord.ProcessingStatus.IN_REVIEW
                if action == "needs_evidence"
                else CandidateRecord.ProcessingStatus.DECIDED
            )
            candidate.save(update_fields=["processing_status", "updated_at"])
            messages.success(request, "The candidate decision was recorded.")
            return redirect("dishes:curator_queue")
        else:
            messages.error(request, "Choose a review action.")

    return render(
        request,
        "dishes/curator_review.html",
        {
            "candidate": candidate,
            "payload": payload,
            "alternatives": ", ".join(alternatives),
            "candidate_name": payload.get("candidate_name", ""),
            "description": _candidate_value(payload, "description"),
            "category": _candidate_value(payload, "category"),
            "matches": candidate.match_suggestions.all(),
            "excerpts": candidate.source.excerpts.all(),
        },
    )

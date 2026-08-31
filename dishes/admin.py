from django.contrib import admin, messages
from django.db import transaction
from django.utils.text import slugify

from .models import (
    CandidateMatch,
    CandidateRecord,
    Dish,
    DishCategory,
    DishClaim,
    DishLocation,
    DishName,
    DishRelationship,
    EvidenceExcerpt,
    Location,
    ReviewDecision,
    ReviewStatus,
    Source,
)
from .services import normalize_name


class DishNameInline(admin.TabularInline):
    model = DishName
    extra = 0


class DishLocationInline(admin.TabularInline):
    model = DishLocation
    extra = 0


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ("canonical_name", "category", "publication_status", "updated_at")
    list_filter = ("publication_status", "category")
    search_fields = ("canonical_name", "names__name", "description")
    prepopulated_fields = {"slug": ("canonical_name",)}
    inlines = (DishNameInline, DishLocationInline)


class CandidateMatchInline(admin.TabularInline):
    model = CandidateMatch
    extra = 0
    readonly_fields = (
        "proposed_dish",
        "proposed_decision",
        "deterministic_score",
        "model_score",
        "model_identifier",
        "rationale",
        "evidence_summary",
    )
    can_delete = False


@admin.action(description="Move selected candidates into human review")
def move_to_review(modeladmin, request, queryset):
    eligible = queryset.filter(processing_status=CandidateRecord.ProcessingStatus.MATCHED)
    updated = eligible.update(processing_status=CandidateRecord.ProcessingStatus.IN_REVIEW)
    modeladmin.message_user(request, f"{updated} candidate(s) moved into review.")


@admin.action(description="Request stronger evidence for selected candidates")
def request_more_evidence(modeladmin, request, queryset):
    count = 0
    for candidate in queryset:
        ReviewDecision.objects.create(
            candidate=candidate,
            reviewer=request.user,
            action=ReviewDecision.Action.NEEDS_EVIDENCE,
            notes="More evidence requested from the candidate review screen.",
        )
        candidate.processing_status = CandidateRecord.ProcessingStatus.IN_REVIEW
        candidate.save(update_fields=["processing_status", "updated_at"])
        count += 1
    modeladmin.message_user(request, f"Evidence requested for {count} candidate(s).")


@admin.action(description="Approve selected candidates as new published dishes")
def approve_as_new_dish(modeladmin, request, queryset):
    approved = 0
    skipped = 0

    for candidate in queryset.select_related("source"):
        payload = candidate.extracted_payload or {}
        name = str(payload.get("candidate_name") or "").strip()
        excerpt = candidate.source.excerpts.first()
        if not name or not excerpt or not candidate.match_suggestions.exists():
            skipped += 1
            continue

        slug = slugify(name)
        if Dish.objects.filter(slug=slug).exists():
            skipped += 1
            continue

        description_data = payload.get("description") or {}
        description = (
            description_data.get("value")
            if isinstance(description_data, dict)
            else str(description_data)
        )
        category_data = payload.get("category") or {}
        category_name = (
            category_data.get("value")
            if isinstance(category_data, dict)
            else str(category_data)
        )

        with transaction.atomic():
            category = None
            if category_name:
                category, _ = DishCategory.objects.get_or_create(name=category_name)
            dish = Dish.objects.create(
                canonical_name=name,
                slug=slug,
                description=description or "",
                category=category,
                publication_status=Dish.PublicationStatus.PUBLISHED,
            )
            DishName.objects.create(
                dish=dish,
                name=name,
                normalized_name=normalize_name(name),
                name_type=DishName.NameType.CANONICAL,
                is_preferred=True,
                review_status=ReviewStatus.REVIEWED,
            )
            if description:
                claim = DishClaim.objects.create(
                    dish=dish,
                    claim_type=DishClaim.ClaimType.DESCRIPTION,
                    value={"text": description},
                    review_status=ReviewStatus.REVIEWED,
                    reviewer_note="Approved from the candidate review screen.",
                )
                claim.evidence.add(excerpt)
            ReviewDecision.objects.create(
                candidate=candidate,
                reviewer=request.user,
                action=ReviewDecision.Action.APPROVE_NEW,
                resulting_dish=dish,
                notes="Approved after evidence and match review.",
                corrected_payload=payload,
            )
            candidate.processing_status = CandidateRecord.ProcessingStatus.DECIDED
            candidate.save(update_fields=["processing_status", "updated_at"])
            approved += 1

    modeladmin.message_user(request, f"{approved} candidate(s) approved and published.")
    if skipped:
        modeladmin.message_user(
            request,
            f"{skipped} candidate(s) skipped: a name, evidence, match suggestion, or unique slug was missing.",
            level=messages.WARNING,
        )


@admin.register(CandidateRecord)
class CandidateRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "processing_status", "extraction_model", "created_at")
    list_filter = ("processing_status", "extraction_model", "source__source_tier")
    search_fields = ("source__title", "submitted_text", "raw_model_response")
    readonly_fields = (
        "source",
        "submitted_text",
        "extraction_model",
        "prompt_version",
        "raw_model_response",
        "extracted_payload",
        "validation_errors",
        "created_at",
        "updated_at",
    )
    actions = (move_to_review, request_more_evidence, approve_as_new_dish)
    inlines = (CandidateMatchInline,)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("title", "publisher", "source_type", "source_tier", "retrieved_at")
    list_filter = ("source_type", "source_tier", "publisher")
    search_fields = ("title", "publisher", "author", "url", "stable_identifier")


@admin.register(ReviewDecision)
class ReviewDecisionAdmin(admin.ModelAdmin):
    list_display = ("candidate", "action", "reviewer", "resulting_dish", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("candidate__source__title", "reviewer__username", "notes")
    readonly_fields = ("candidate", "reviewer", "action", "resulting_dish", "created_at", "updated_at")


admin.site.register(
    [
        DishCategory,
        DishClaim,
        DishRelationship,
        EvidenceExcerpt,
        Location,
    ]
)

admin.site.site_header = "African Dishes Curator Admin"
admin.site.site_title = "African Dishes"
admin.site.index_title = "Evidence and review workspace"

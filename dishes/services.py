import copy
import re

from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils.text import slugify

from .models import (
    CandidateRecord,
    Dish,
    DishClaim,
    DishLocation,
    DishName,
    DishCategory,
    ReviewDecision,
    ReviewStatus,
)


PUBLIC_REVIEW_STATUSES = [ReviewStatus.REVIEWED, ReviewStatus.CORROBORATED]


def normalize_name(value):
    """Return a conservative, deterministic form for candidate matching."""
    return re.sub(r"[^\w\s]", "", value.casefold()).strip()


def _payload_value(payload, key):
    value = payload.get(key)
    if isinstance(value, dict):
        return value.get("value")
    return value


def _payload_alternatives(payload):
    alternatives = []
    for item in payload.get("alternative_names") or []:
        if isinstance(item, dict):
            name = item.get("name") or item.get("value")
        else:
            name = item
        name = str(name or "").strip()
        if name:
            alternatives.append(name)
    return alternatives


def approve_candidate_as_new_dish(candidate, reviewer, corrected_payload=None, notes=""):
    """Publish one candidate after an explicit human approval decision.

    The candidate payload is treated as a proposal. Only the edited values
    supplied by the reviewer are copied into the public domain records.
    """
    if candidate.processing_status == CandidateRecord.ProcessingStatus.DECIDED:
        raise ValueError("This candidate already has a recorded decision.")

    payload = copy.deepcopy(candidate.extracted_payload or {})
    if corrected_payload:
        payload.update(corrected_payload)

    name = str(payload.get("candidate_name") or "").strip()
    excerpt = candidate.source.excerpts.order_by("created_at").first()
    if not name:
        raise ValueError("A candidate name is required before publication.")
    if not excerpt:
        raise ValueError("An evidence excerpt is required before publication.")
    if not candidate.match_suggestions.exists():
        raise ValueError("Generate a match suggestion before publication.")

    slug = slugify(name) or str(candidate.id)
    if Dish.objects.filter(slug=slug).exists():
        raise ValueError(f"A dish with the slug '{slug}' already exists.")

    wikidata_id = str(payload.get("wikidata_id") or "").strip().upper() or None
    if wikidata_id and Dish.objects.filter(wikidata_id=wikidata_id).exists():
        raise ValueError(f"Wikidata entity {wikidata_id} is already linked to a dish.")

    description = str(_payload_value(payload, "description") or "").strip()
    category_name = str(_payload_value(payload, "category") or "").strip()
    alternatives = []
    seen_names = {normalize_name(name)}
    for alternative in _payload_alternatives(payload):
        normalized = normalize_name(alternative)
        if normalized and normalized not in seen_names:
            alternatives.append(alternative)
            seen_names.add(normalized)

    with transaction.atomic():
        category = None
        if category_name:
            category, _ = DishCategory.objects.get_or_create(name=category_name)

        dish = Dish.objects.create(
            canonical_name=name,
            slug=slug,
            wikidata_id=wikidata_id,
            description=description,
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

        for alternative in alternatives:
            DishName.objects.create(
                dish=dish,
                name=alternative,
                normalized_name=normalize_name(alternative),
                language_code="en",
                name_type=DishName.NameType.ALTERNATIVE,
                review_status=ReviewStatus.REVIEWED,
            )
            claim = DishClaim.objects.create(
                dish=dish,
                claim_type=DishClaim.ClaimType.NAME_EQUIVALENCE,
                value={
                    "canonical_name": name,
                    "alternative_name": alternative,
                    "language_code": "en",
                },
                review_status=ReviewStatus.REVIEWED,
                reviewer_note="Alternative name accepted by a human reviewer.",
            )
            claim.evidence.add(excerpt)

        if description:
            claim = DishClaim.objects.create(
                dish=dish,
                claim_type=DishClaim.ClaimType.DESCRIPTION,
                value={"text": description},
                review_status=ReviewStatus.REVIEWED,
                reviewer_note="Description accepted by a human reviewer.",
            )
            claim.evidence.add(excerpt)

        if category_name:
            claim = DishClaim.objects.create(
                dish=dish,
                claim_type=DishClaim.ClaimType.CATEGORY,
                value={"name": category_name},
                review_status=ReviewStatus.REVIEWED,
                reviewer_note="Category accepted by a human reviewer.",
            )
            claim.evidence.add(excerpt)

        ReviewDecision.objects.create(
            candidate=candidate,
            reviewer=reviewer,
            action=ReviewDecision.Action.EDIT_APPROVE if corrected_payload else ReviewDecision.Action.APPROVE_NEW,
            resulting_dish=dish,
            notes=notes or "Approved after reviewing the structured candidate, evidence and match suggestion.",
            corrected_payload=payload if corrected_payload else None,
        )
        candidate.processing_status = CandidateRecord.ProcessingStatus.DECIDED
        candidate.save(update_fields=["processing_status", "updated_at"])

    return dish


def public_dishes(query="", location="", category=""):
    queryset = (
        Dish.objects.filter(publication_status=Dish.PublicationStatus.PUBLISHED)
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "names",
                queryset=DishName.objects.filter(review_status__in=PUBLIC_REVIEW_STATUSES),
            ),
            Prefetch(
                "locations",
                queryset=DishLocation.objects.filter(
                    review_status__in=PUBLIC_REVIEW_STATUSES
                ).select_related("location"),
            ),
            Prefetch(
                "claims",
                queryset=DishClaim.objects.filter(
                    review_status__in=PUBLIC_REVIEW_STATUSES
                ).prefetch_related("evidence__source"),
            ),
        )
        .order_by("canonical_name")
    )

    if query:
        queryset = queryset.filter(
            Q(canonical_name__icontains=query)
            | Q(names__name__icontains=query)
            | Q(names__normalized_name__icontains=normalize_name(query))
        )
    if location:
        queryset = queryset.filter(locations__location__name=location)
    if category:
        queryset = queryset.filter(category__slug=category)

    return queryset.distinct()


def serialize_dish(dish):
    names = list(dish.names.all())
    location_links = list(dish.locations.all())
    claims = list(dish.claims.all())

    evidence = []
    for claim in claims:
        for excerpt in claim.evidence.all():
            evidence.append(
                {
                    "claim_type": claim.get_claim_type_display(),
                    "claim": claim.value,
                    "excerpt": excerpt.text,
                    "locator": excerpt.locator,
                    "source": {
                        "title": excerpt.source.title,
                        "url": excerpt.source.url,
                        "publisher": excerpt.source.publisher,
                        "tier": excerpt.source.source_tier,
                        "citation": excerpt.source.citation_text,
                    },
                }
            )

    return {
        "id": str(dish.id),
        "canonical_name": dish.canonical_name,
        "slug": dish.slug,
        "wikidata_id": dish.wikidata_id,
        "wikidata_url": (
            f"https://www.wikidata.org/wiki/{dish.wikidata_id}"
            if dish.wikidata_id
            else None
        ),
        "description": dish.description,
        "category": dish.category.name if dish.category else None,
        "review_status": "reviewed",
        "alternative_names": [
            {
                "name": name.name,
                "language_code": name.language_code or None,
                "type": name.name_type,
            }
            for name in names
            if name.name_type != DishName.NameType.CANONICAL
        ],
        "locations": [
            {
                "name": link.location.name,
                "relationship": link.relationship,
            }
            for link in location_links
        ],
        "evidence": evidence,
    }

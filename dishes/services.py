import re

from django.db.models import Prefetch, Q

from .models import Dish, DishClaim, DishLocation, DishName, ReviewStatus


PUBLIC_REVIEW_STATUSES = [ReviewStatus.REVIEWED, ReviewStatus.CORROBORATED]


def normalize_name(value):
    """Return a conservative, deterministic form for candidate matching."""
    return re.sub(r"[^\w\s]", "", value.casefold()).strip()


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

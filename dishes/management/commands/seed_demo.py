from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from dishes.demo_data import DISHES, SOURCES
from dishes.category_data import LEGACY_CATEGORY_MAP
from dishes.models import (
    CandidateRecord,
    Dish,
    DishCategory,
    DishClaim,
    DishLocation,
    DishName,
    EvidenceExcerpt,
    Location,
    ReviewDecision,
    ReviewStatus,
    Source,
)
from dishes.services import normalize_name


class Command(BaseCommand):
    help = "Create the source-linked Ghana pilot dataset used by the demo."

    def handle(self, *args, **options):
        reviewer, _ = get_user_model().objects.get_or_create(username="demo-curator")
        reviewer.set_unusable_password()
        reviewer.save(update_fields=["password"])

        ghana, _ = Location.objects.get_or_create(
            name="Ghana",
            location_type=Location.LocationType.COUNTRY,
            parent=None,
            defaults={"iso_code": "GH"},
        )

        source_records = {}
        for key, item in SOURCES.items():
            source, _ = Source.objects.get_or_create(
                url=item["url"],
                defaults={
                    "title": item["title"],
                    "publisher": item["publisher"],
                    "source_type": Source.SourceType.GOVERNMENT,
                    "source_tier": Source.SourceTier.A,
                    "retrieved_at": timezone.now(),
                    "citation_text": item["citation"],
                    "notes": "Pilot source. Public claims still require recorded human review.",
                },
            )
            source_records[key] = source

        created_count = 0
        for item in DISHES:
            category_name = LEGACY_CATEGORY_MAP.get(item["category"], item["category"])
            category, _ = DishCategory.objects.get_or_create(name=category_name)
            if item["location"] == "Ghana":
                location = ghana
            else:
                location, _ = Location.objects.get_or_create(
                    name=item["location"],
                    location_type=Location.LocationType.REGION,
                    parent=ghana,
                )

            slug = slugify(item["name"])
            dish, created = Dish.objects.get_or_create(
                slug=slug,
                defaults={"canonical_name": item["name"]},
            )
            dish.canonical_name = item["name"]
            dish.description = item["description"]
            dish.category = category
            dish.publication_status = Dish.PublicationStatus.PUBLISHED
            dish.save()
            created_count += int(created)

            DishName.objects.update_or_create(
                dish=dish,
                normalized_name=normalize_name(item["name"]),
                language_code="",
                name_type=DishName.NameType.CANONICAL,
                defaults={
                    "name": item["name"],
                    "is_preferred": True,
                    "review_status": ReviewStatus.REVIEWED,
                },
            )
            for alternative_name in item["alternative_names"]:
                name_type = (
                    DishName.NameType.ABBREVIATION
                    if alternative_name.isupper()
                    else DishName.NameType.ALTERNATIVE
                )
                DishName.objects.update_or_create(
                    dish=dish,
                    normalized_name=normalize_name(alternative_name),
                    language_code="",
                    name_type=name_type,
                    defaults={
                        "name": alternative_name,
                        "is_preferred": False,
                        "review_status": ReviewStatus.REVIEWED,
                    },
                )

            DishLocation.objects.update_or_create(
                dish=dish,
                location=location,
                relationship=DishLocation.Relationship.ASSOCIATED_WITH,
                defaults={"review_status": ReviewStatus.REVIEWED},
            )

            source = source_records[item["source"]]
            excerpt, _ = EvidenceExcerpt.objects.get_or_create(
                source=source,
                locator=item["locator"],
                text=item["excerpt"],
                defaults={"language_code": "en"},
            )

            description_claim, _ = DishClaim.objects.get_or_create(
                dish=dish,
                claim_type=DishClaim.ClaimType.DESCRIPTION,
                value={"text": item["description"]},
                defaults={
                    "review_status": ReviewStatus.REVIEWED,
                    "reviewer_note": "Seeded for the application demo from a government source.",
                },
            )
            description_claim.evidence.add(excerpt)

            if item["alternative_names"]:
                name_claim, _ = DishClaim.objects.get_or_create(
                    dish=dish,
                    claim_type=DishClaim.ClaimType.NAME_EQUIVALENCE,
                    value={
                        "canonical": item["name"],
                        "alternative_names": item["alternative_names"],
                    },
                    defaults={
                        "review_status": ReviewStatus.REVIEWED,
                        "reviewer_note": "Seeded for the application demo from a government source.",
                    },
                )
                name_claim.evidence.add(excerpt)

            candidate, _ = CandidateRecord.objects.get_or_create(
                source=source,
                submitted_text=item["excerpt"],
                defaults={
                    "extraction_model": "demo-structured-candidate-v1",
                    "prompt_version": "demo-v1",
                    "extracted_payload": {
                        "candidate_name": item["name"],
                        "description": item["description"],
                        "alternative_names": item["alternative_names"],
                        "location": item["location"],
                    },
                    "processing_status": CandidateRecord.ProcessingStatus.DECIDED,
                },
            )
            ReviewDecision.objects.get_or_create(
                candidate=candidate,
                reviewer=reviewer,
                action=ReviewDecision.Action.APPROVE_NEW,
                resulting_dish=dish,
                defaults={
                    "notes": "Human-reviewed demo decision. Cultural validation remains ongoing.",
                    "corrected_payload": candidate.extracted_payload,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo ready: {len(DISHES)} published records ({created_count} newly created)."
            )
        )

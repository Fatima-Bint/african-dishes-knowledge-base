import re

from django.core.management.base import BaseCommand, CommandError

from dishes.models import CandidateRecord


IGNORED_LINES = {
    "ghanaian cuisine",
    "main staple foods",
    "foods made with maize",
    "foods made with rice",
    "foods made with cassava",
    "foods made with beans",
    "foods made with yam",
    "soups and stews",
    "breakfast",
    "sweet foods",
    "beverages",
    "street foods in ghana",
    "common ghanaian dishes",
    "see also",
    "references",
    "further reading",
}


def possible_dish_names(text, limit=100):
    names = []
    seen = set()

    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip(" •-*–—")
        if not line or len(line) < 2 or len(line) > 90:
            continue

        normalised = line.casefold()
        if normalised in IGNORED_LINES or normalised in seen:
            continue
        if line[0].isdigit() or line.startswith("["):
            continue
        if any(marker in normalised for marker in ("edit", "citation needed", "isbn")):
            continue
        if line.endswith((".", ":", ";")):
            continue

        seen.add(normalised)
        names.append(line)
        if len(names) >= limit:
            break

    return names


class Command(BaseCommand):
    help = "Create reviewable dish-name suggestions from a stored candidate."

    def add_arguments(self, parser):
        parser.add_argument("candidate_id")

    def handle(self, *args, **options):
        try:
            candidate = CandidateRecord.objects.get(id=options["candidate_id"])
        except CandidateRecord.DoesNotExist as exc:
            raise CommandError("Candidate record was not found.") from exc

        names = possible_dish_names(candidate.submitted_text)
        if not names:
            raise CommandError("No possible dish names were found.")

        candidate.extracted_payload = {
            "extraction_method": "deterministic_baseline_v1",
            "review_status": "needs_review",
            "candidate_dishes": [
                {
                    "name": name,
                    "evidence": name,
                    "status": "needs_review",
                }
                for name in names
            ],
            "notes": (
                "These are machine-generated suggestions from page structure. "
                "They must be reviewed against the source before publication."
            ),
        }
        candidate.extraction_model = "deterministic-baseline-v1"
        candidate.processing_status = CandidateRecord.ProcessingStatus.EXTRACTED
        candidate.save(
            update_fields=[
                "extracted_payload",
                "extraction_model",
                "processing_status",
                "updated_at",
            ]
        )

        self.stdout.write(self.style.SUCCESS(
            f"Created {len(names)} reviewable dish-name suggestions."
        ))
        self.stdout.write(
            "Open the candidate in Admin and inspect its extracted payload."
        )

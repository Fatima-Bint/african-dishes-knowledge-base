import json
import re
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from dishes.models import CandidateRecord, EvidenceExcerpt, Source


QID_PATTERN = re.compile(r"^Q\d+$", re.IGNORECASE)


def fetch_entity(qid):
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid.upper()}.json"
    request = Request(url, headers={"User-Agent": "AfricanDishesKnowledgeBase/0.2"})
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except Exception as error:
        raise CommandError(f"Could not retrieve Wikidata entity: {error}") from error

    entity = payload.get("entities", {}).get(qid.upper())
    if not entity or "missing" in entity:
        raise CommandError(f"Wikidata entity {qid.upper()} was not found.")
    return entity


def language_value(mapping, language="en"):
    item = mapping.get(language) or {}
    return item.get("value")


class Command(BaseCommand):
    help = "Register one Wikidata entity as a structured, review-only candidate."

    def add_arguments(self, parser):
        parser.add_argument("qid", help="Exact Wikidata entity ID, for example Q12345")

    def handle(self, *args, **options):
        qid = options["qid"].upper().strip()
        if not QID_PATTERN.fullmatch(qid):
            raise CommandError("Provide an exact Wikidata QID such as Q12345.")

        entity = fetch_entity(qid)
        label = language_value(entity.get("labels", {}))
        if not label:
            raise CommandError("The entity has no English label; review another language manually.")

        aliases = [
            item["value"]
            for item in entity.get("aliases", {}).get("en", [])
            if item.get("value")
        ]
        description = language_value(entity.get("descriptions", {}))
        wikipedia_title = (
            entity.get("sitelinks", {}).get("enwiki", {}).get("title")
        )
        entity_url = f"https://www.wikidata.org/wiki/{qid}"

        source, _ = Source.objects.get_or_create(
            stable_identifier=qid,
            defaults={
                "title": f"Wikidata entity {qid}: {label}",
                "url": entity_url,
                "publisher": "Wikimedia Foundation",
                "source_type": Source.SourceType.WIKIDATA,
                "source_tier": Source.SourceTier.B,
                "retrieved_at": timezone.now(),
                "licence_name": "CC0 1.0",
                "licence_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                "citation_text": f"Wikidata contributors. {label} ({qid}).",
                "notes": "Structured public reference. Human review is required before publication.",
            },
        )

        structured_excerpt = {
            "qid": qid,
            "label": label,
            "description": description,
            "aliases": aliases,
            "english_wikipedia_title": wikipedia_title,
        }
        excerpt, _ = EvidenceExcerpt.objects.get_or_create(
            source=source,
            locator="English label, aliases, description and sitelink",
            defaults={
                "text": json.dumps(structured_excerpt, ensure_ascii=False, indent=2),
                "language_code": "en",
            },
        )

        candidate = CandidateRecord.objects.create(
            source=source,
            submitted_text=excerpt.text,
            extraction_model="wikidata-structured-ingestion-v1",
            prompt_version="not-applicable",
            extracted_payload={
                "candidate_name": label,
                "description": {
                    "value": description,
                    "evidence": description,
                },
                "alternative_names": [
                    {"name": alias, "language_code": "en", "evidence": alias}
                    for alias in aliases
                ],
                "location_claims": [],
                "category": {"value": None, "evidence": None},
                "ingredient_mentions": [],
                "ambiguities": [
                    "Wikidata labels and aliases do not establish cultural origin or equivalence."
                ],
                "unsupported_or_missing_fields": [
                    "location claims",
                    "category",
                    "ingredient mentions",
                ],
                "wikidata_id": qid,
                "english_wikipedia_title": wikipedia_title,
            },
            processing_status=CandidateRecord.ProcessingStatus.EXTRACTED,
        )

        self.stdout.write(self.style.SUCCESS("Wikidata candidate registered."))
        self.stdout.write(f"Candidate: {candidate.id}")
        self.stdout.write(f"Label: {label}")
        self.stdout.write("Next: run suggest_matches, then review the candidate in Admin.")

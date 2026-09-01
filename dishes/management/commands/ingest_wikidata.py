import json
import re
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from dishes.models import CandidateRecord, EvidenceExcerpt, Source


QID_PATTERN = re.compile(r"^Q\d+$", re.IGNORECASE)
TRACKED_PROPERTIES = ("P31", "P495", "P2341", "P1705", "P2012")


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


def snak_value(snak):
    data_value = (snak or {}).get("datavalue", {}).get("value")
    if isinstance(data_value, dict):
        return (
            data_value.get("id")
            or data_value.get("text")
            or data_value.get("time")
            or data_value.get("amount")
        )
    return data_value


def reference_urls(statement):
    urls = []
    for reference in statement.get("references", []):
        for snaks in reference.get("snaks", {}).values():
            for snak in snaks:
                if snak.get("property") not in {"P854", "P973"}:
                    continue
                value = snak_value(snak)
                if value and str(value).startswith(("http://", "https://")):
                    urls.append(str(value))
    return sorted(set(urls))


def selected_claims(entity):
    claims = []
    for property_id in TRACKED_PROPERTIES:
        for statement in entity.get("claims", {}).get(property_id, []):
            if statement.get("rank") == "deprecated":
                continue
            mainsnak = statement.get("mainsnak", {})
            value = snak_value(mainsnak)
            if value is not None:
                claims.append(
                    {
                        "property": property_id,
                        "value": value,
                        "references": reference_urls(statement),
                    }
                )
    return claims


def register_entity(entity):
    """Persist one API entity as a review-only candidate."""
    qid = str(entity.get("id") or "").upper().strip()
    if not QID_PATTERN.fullmatch(qid):
        raise CommandError("Wikidata returned an entity without a valid QID.")

    label = language_value(entity.get("labels", {}))
    if not label:
        raise CommandError(
            "The entity has no English label; review another language manually."
        )

    aliases = [
        item["value"]
        for item in entity.get("aliases", {}).get("en", [])
        if item.get("value")
    ]
    description = language_value(entity.get("descriptions", {}))
    wikipedia_title = entity.get("sitelinks", {}).get("enwiki", {}).get("title")
    claims = selected_claims(entity)
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
        "selected_claims": claims,
    }
    excerpt, _ = EvidenceExcerpt.objects.get_or_create(
        source=source,
        locator="English label, aliases, description and sitelink",
        defaults={
            "text": json.dumps(structured_excerpt, ensure_ascii=False, indent=2),
            "language_code": "en",
        },
    )

    existing = (
        CandidateRecord.objects.filter(
            source=source,
            extracted_payload__wikidata_id=qid,
        )
        .order_by("-created_at")
        .first()
    )
    if existing:
        return existing, False, label

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
                    "cultural origin and name equivalence require human review",
                ],
                "wikidata_id": qid,
                "english_wikipedia_title": wikipedia_title,
                "selected_claims": claims,
        },
        processing_status=CandidateRecord.ProcessingStatus.EXTRACTED,
    )
    return candidate, True, label


class Command(BaseCommand):
    help = "Register exact Wikidata entity IDs as structured, review-only candidates."

    def add_arguments(self, parser):
        parser.add_argument(
            "qids",
            nargs="+",
            help="One or more exact Wikidata entity IDs, for example Q12345",
        )

    def handle(self, *args, **options):
        qids = [qid.upper().strip() for qid in options["qids"]]
        for qid in qids:
            if not QID_PATTERN.fullmatch(qid):
                raise CommandError("Provide exact Wikidata QIDs such as Q12345.")

        for qid in qids:
            candidate, created, label = register_entity(fetch_entity(qid))
            state = "registered" if created else "already registered"
            self.stdout.write(self.style.SUCCESS(f"Wikidata candidate {state}."))
            self.stdout.write(f"Candidate: {candidate.id}")
            self.stdout.write(f"Label: {label} ({qid})")

        self.stdout.write(
            "Next: run suggest_matches for each candidate, then open the review queue."
        )

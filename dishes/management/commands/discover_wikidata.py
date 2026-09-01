import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError

from .ingest_wikidata import QID_PATTERN, fetch_entity, register_entity


SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"


def discover_entities(country_qid, limit):
    query = f"""
SELECT DISTINCT ?item ?itemLabel ?description WHERE {{
  ?item wdt:P31/wdt:P279* wd:Q746549.
  {{ ?item wdt:P495 wd:{country_qid}. }}
  UNION
  {{ ?item wdt:P2341 wd:{country_qid}. }}
  OPTIONAL {{ ?item schema:description ?description . FILTER(LANG(?description) = "en") }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
ORDER BY ?itemLabel
LIMIT {limit}
"""
    url = f"{SPARQL_ENDPOINT}?{urlencode({'query': query, 'format': 'json'})}"
    request = Request(
        url,
        headers={
            "Accept": "application/sparql-results+json",
            "User-Agent": "AfricanDishesKnowledgeBase/0.3",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except Exception as error:
        raise CommandError(f"Could not query Wikidata discovery service: {error}") from error

    rows = []
    for row in payload.get("results", {}).get("bindings", []):
        item_url = row.get("item", {}).get("value", "")
        qid = item_url.rstrip("/").rsplit("/", 1)[-1].upper()
        if QID_PATTERN.fullmatch(qid):
            rows.append(
                {
                    "qid": qid,
                    "label": row.get("itemLabel", {}).get("value", qid),
                    "description": row.get("description", {}).get("value", ""),
                }
            )
    return rows


class Command(BaseCommand):
    help = "Discover Ghana-linked Wikidata dish entities and optionally register candidates."

    def add_arguments(self, parser):
        parser.add_argument(
            "--country",
            default="Q117",
            help="Wikidata country QID to search, default Q117 (Ghana).",
        )
        parser.add_argument("--limit", type=int, default=12)
        parser.add_argument(
            "--ingest",
            action="store_true",
            help="Register discovered QIDs as review-only candidates.",
        )

    def handle(self, *args, **options):
        country_qid = options["country"].upper().strip()
        if not QID_PATTERN.fullmatch(country_qid):
            raise CommandError("Provide an exact country QID such as Q117.")
        if options["limit"] < 1 or options["limit"] > 100:
            raise CommandError("Limit must be between 1 and 100.")

        rows = discover_entities(country_qid, options["limit"])
        if not rows:
            self.stdout.write("No Ghana-linked dish entities were returned.")
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {len(rows)} structured Wikidata dish candidate(s) for {country_qid}."
            )
        )
        for row in rows:
            description = f" — {row['description']}" if row["description"] else ""
            self.stdout.write(f"{row['qid']} — {row['label']}{description}")

        if options["ingest"]:
            self.stdout.write("Registering candidates for human review…")
            for row in rows:
                candidate, created, label = register_entity(fetch_entity(row["qid"]))
                state = "created" if created else "already existed"
                self.stdout.write(f"{candidate.id} — {label} ({state})")
        else:
            self.stdout.write(
                "Next: run ingest_wikidata with selected QIDs; discovery does not publish anything."
            )

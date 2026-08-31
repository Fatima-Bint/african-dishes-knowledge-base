import json
from html.parser import HTMLParser
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from dishes.models import CandidateRecord, EvidenceExcerpt, Source


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip = True
        if tag in {"p", "li", "h1", "h2", "h3", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.skip = False
        if tag in {"p", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def get_text(self):
        lines = [
            " ".join(line.split())
            for line in "".join(self.parts).splitlines()
        ]
        return "\n".join(line for line in lines if line).strip()


def fetch_wikipedia_page(title):
    api_url = "https://en.wikipedia.org/w/api.php?" + urlencode({
        "action": "parse",
        "page": title,
        "prop": "text|info",
        "inprop": "url",
        "format": "json",
        "formatversion": "2",
    })

    request = Request(
        api_url,
        headers={
            "User-Agent": "AfricanDishesKnowledgeBase/0.1"
        },
    )

    try:
        with urlopen(request, timeout=20) as response:
            data = json.load(response)
    except Exception as error:
        raise CommandError(f"Could not retrieve Wikipedia page: {error}")

    if "error" in data:
        raise CommandError(data["error"]["info"])

    return data["parse"]


class Command(BaseCommand):
    help = "Register a Wikipedia page and create a candidate record."

    def add_arguments(self, parser):
        parser.add_argument("title")

    def handle(self, *args, **options):
        title = options["title"]
        page = fetch_wikipedia_page(title)

        extractor = TextExtractor()
        extractor.feed(page["text"])
        page_text = extractor.get_text()

        if not page_text:
            raise CommandError("No readable text was found.")

        source_url = page.get(
            "fullurl",
            f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
        )

        source, _ = Source.objects.get_or_create(
            url=source_url,
            defaults={
                "title": page.get("title", title),
                "stable_identifier": str(page.get("pageid", "")),
                "publisher": "Wikipedia",
                "source_type": Source.SourceType.WIKIPEDIA,
                "source_tier": Source.SourceTier.D,
                "retrieved_at": timezone.now(),
                "licence_name": "CC BY-SA",
                "licence_url": (
                    "https://creativecommons.org/licenses/by-sa/4.0/"
                ),
                "citation_text": f"{page.get('title', title)} — Wikipedia",
                "notes": (
                    "Discovery source only. Claims require review "
                    "and corroboration."
                ),
            },
        )

        EvidenceExcerpt.objects.get_or_create(
            source=source,
            locator="Retrieved page text",
            defaults={"text": page_text[:12000]},
        )

        candidate = CandidateRecord.objects.create(
            source=source,
            submitted_text=page_text,
            processing_status=CandidateRecord.ProcessingStatus.RECEIVED,
        )

        self.stdout.write(self.style.SUCCESS(
            "Wikipedia source registered successfully."
        ))
        self.stdout.write(f"Source: {source.title}")
        self.stdout.write(f"Candidate created: {candidate.id}")
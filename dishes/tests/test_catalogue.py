import csv
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from dishes.models import Dish


class PublicCatalogueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def test_catalogue_displays_only_published_records(self):
        Dish.objects.create(
            canonical_name="Unreviewed Draft",
            publication_status=Dish.PublicationStatus.DRAFT,
        )

        response = self.client.get(reverse("dishes:catalogue"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ga Kenkey")
        self.assertNotContains(response, "Unreviewed Draft")

    def test_alternative_name_search_finds_canonical_record(self):
        response = self.client.get(reverse("dishes:catalogue"), {"q": "Komi"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ga Kenkey")
        self.assertNotContains(response, "Fante Kenkey")

    def test_api_returns_reviewed_records_and_evidence(self):
        response = self.client.get(reverse("dishes:api_dishes"), {"q": "Aprapransa"})
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["results"][0]["canonical_name"], "Akplijii")
        self.assertTrue(payload["results"][0]["evidence"])
        self.assertEqual(payload["results"][0]["review_status"], "reviewed")

    def test_detail_page_renders_claim_level_provenance(self):
        response = self.client.get(reverse("dishes:detail", args=["akplijii"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Claim-level provenance")
        self.assertContains(response, "Open source")
        self.assertContains(response, "Aprapransa")

    def test_csv_export_contains_source_urls(self):
        response = self.client.get(reverse("dishes:export_csv"), {"q": "TZ"})
        rows = list(csv.DictReader(StringIO(response.content.decode("utf-8"))))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["canonical_name"], "Tuo Zaafi")
        self.assertIn("ghanaculture.gov.gh", rows[0]["source_urls"])

    def test_seed_command_is_idempotent(self):
        before = Dish.objects.count()
        call_command("seed_demo", verbosity=0)
        self.assertEqual(Dish.objects.count(), before)

    def test_public_navigation_uses_catalogue_anchor_and_hides_api(self):
        response = self.client.get(reverse("dishes:catalogue"))
        html = response.content.decode("utf-8")

        self.assertIn('href="/#catalogue">Catalogue</a>', html)
        self.assertIn('href="/demo/">Demo</a>', html)
        self.assertIn('href="/admin/">Curator admin</a>', html)
        self.assertNotIn('>API</a>', html)
        self.assertNotIn('>Review queue</a>', html)

    def test_demo_page_shows_placeholder_without_video_id(self):
        response = self.client.get(reverse("dishes:demo"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo video coming soon")

    @override_settings(DEMO_VIDEO_ID="abcdefghijk")
    def test_demo_page_embeds_configured_youtube_video(self):
        response = self.client.get(reverse("dishes:demo"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "https://www.youtube-nocookie.com/embed/abcdefghijk",
        )

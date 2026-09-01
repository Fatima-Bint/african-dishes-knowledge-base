from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from dishes.forms import CandidateRecordReviewForm
from dishes.models import CandidateRecord, Dish, ReviewDecision


WIKIDATA_ENTITY = {
    "id": "Q12345",
    "labels": {"en": {"language": "en", "value": "Example Ghana Dish"}},
    "aliases": {"en": [{"language": "en", "value": "Example Local Name"}]},
    "descriptions": {"en": {"language": "en", "value": "A structured example dish."}},
    "sitelinks": {"enwiki": {"title": "Example Ghana Dish"}},
}


class WikidataWorkflowTests(TestCase):
    def setUp(self):
        self.reviewer = get_user_model().objects.create_user(
            username="staff-reviewer",
            password="test-password",
            is_staff=True,
            is_superuser=True,
        )

    @patch("dishes.management.commands.ingest_wikidata.fetch_entity")
    def test_exact_qid_ingestion_is_review_only_and_idempotent(self, fetch_entity):
        fetch_entity.return_value = WIKIDATA_ENTITY

        call_command("ingest_wikidata", "Q12345", verbosity=0)
        call_command("ingest_wikidata", "Q12345", verbosity=0)

        candidate = CandidateRecord.objects.get()
        self.assertEqual(candidate.extracted_payload["wikidata_id"], "Q12345")
        self.assertEqual(candidate.processing_status, CandidateRecord.ProcessingStatus.EXTRACTED)
        self.assertEqual(Dish.objects.count(), 0)
        self.assertEqual(fetch_entity.call_count, 2)

    @patch("dishes.management.commands.discover_wikidata.discover_entities")
    def test_discovery_lists_candidates_without_publishing(self, discover_entities):
        discover_entities.return_value = [
            {"qid": "Q12345", "label": "Example Ghana Dish", "description": "A dish."}
        ]

        call_command("discover_wikidata", "--limit", "1", verbosity=0)

        self.assertEqual(CandidateRecord.objects.count(), 0)
        self.assertEqual(Dish.objects.count(), 0)

    @patch("dishes.management.commands.ingest_wikidata.fetch_entity")
    def test_staff_review_can_edit_and_publish_candidate(self, fetch_entity):
        fetch_entity.return_value = WIKIDATA_ENTITY
        call_command("ingest_wikidata", "Q12345", verbosity=0)
        candidate = CandidateRecord.objects.get()
        call_command("suggest_matches", str(candidate.id), verbosity=0)

        self.client.force_login(self.reviewer)
        response = self.client.get(
            reverse("dishes:curator_review", args=[candidate.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Example Ghana Dish")
        self.assertContains(response, "Q12345")

        response = self.client.post(
            reverse("dishes:curator_review", args=[candidate.id]),
            {
                "action": "approve_new",
                "candidate_name": "Reviewed Ghana Dish",
                "description": "A reviewer-approved description.",
                "category": "Staple",
                "alternative_names": "Approved Local Name",
                "notes": "Checked the structured entity and retained uncertainty about origin.",
            },
        )

        self.assertEqual(response.status_code, 302)
        dish = Dish.objects.get()
        self.assertEqual(dish.canonical_name, "Reviewed Ghana Dish")
        self.assertEqual(dish.wikidata_id, "Q12345")
        self.assertEqual(dish.publication_status, Dish.PublicationStatus.PUBLISHED)
        self.assertEqual(candidate.refresh_from_db(), None)
        self.assertEqual(candidate.processing_status, CandidateRecord.ProcessingStatus.DECIDED)
        self.assertEqual(
            ReviewDecision.objects.get(candidate=candidate).reviewer,
            self.reviewer,
        )

    def test_non_staff_cannot_open_review_queue(self):
        response = self.client.get(reverse("dishes:curator_queue"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    @patch("dishes.management.commands.ingest_wikidata.fetch_entity")
    def test_admin_candidate_form_exposes_editable_proposal_fields(self, fetch_entity):
        fetch_entity.return_value = WIKIDATA_ENTITY
        call_command("ingest_wikidata", "Q12345", verbosity=0)
        candidate = CandidateRecord.objects.get()

        self.client.force_login(self.reviewer)
        response = self.client.get(
            reverse("admin:dishes_candidaterecord_change", args=[candidate.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Proposed canonical name")
        self.assertContains(response, "Example Local Name")

        form = CandidateRecordReviewForm(
            data={
                "processing_status": CandidateRecord.ProcessingStatus.MATCHED,
                "candidate_name": "Reviewed Plasas",
                "description": "A reviewer-edited description.",
                "category": "Leafy soup",
                "alternative_names": "Palava sauce",
            },
            instance=candidate,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        candidate.refresh_from_db()
        self.assertEqual(candidate.extracted_payload["candidate_name"], "Reviewed Plasas")
        self.assertEqual(
            candidate.extracted_payload["alternative_names"][0]["name"],
            "Palava sauce",
        )

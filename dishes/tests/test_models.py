from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from dishes.models import (
    CandidateRecord,
    Dish,
    DishName,
    DishRelationship,
    EvidenceExcerpt,
    ReviewDecision,
    Source,
)


class FoundationModelTests(TestCase):
    def setUp(self):
        self.source = Source.objects.create(
            title="Test institutional source",
            url="https://example.org/test-source",
            source_type=Source.SourceType.INSTITUTIONAL,
            source_tier=Source.SourceTier.A,
            retrieved_at=timezone.now(),
        )

    def test_candidate_remains_separate_from_published_dish(self):
        candidate = CandidateRecord.objects.create(
            source=self.source,
            submitted_text="A source excerpt about a candidate dish.",
        )
        published_dish = Dish.objects.create(
            canonical_name="Reviewed Dish",
            publication_status=Dish.PublicationStatus.PUBLISHED,
        )

        self.assertEqual(candidate.processing_status, CandidateRecord.ProcessingStatus.RECEIVED)
        self.assertNotEqual(str(candidate.id), str(published_dish.id))

    def test_dish_name_form_is_unique_within_dish(self):
        dish = Dish.objects.create(canonical_name="Example Dish")
        DishName.objects.create(
            dish=dish,
            name="Example Dish",
            normalized_name="example dish",
            language_code="en",
            name_type=DishName.NameType.CANONICAL,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            DishName.objects.create(
                dish=dish,
                name="EXAMPLE DISH",
                normalized_name="example dish",
                language_code="en",
                name_type=DishName.NameType.CANONICAL,
            )

    def test_dish_cannot_relate_to_itself(self):
        dish = Dish.objects.create(canonical_name="Example Dish")

        with self.assertRaises(IntegrityError), transaction.atomic():
            DishRelationship.objects.create(
                source_dish=dish,
                target_dish=dish,
                relationship_type=DishRelationship.RelationshipType.RELATED_TO,
            )

    def test_review_decision_records_human_reviewer(self):
        candidate = CandidateRecord.objects.create(
            source=self.source,
            submitted_text="A source excerpt about a candidate dish.",
        )
        reviewer = get_user_model().objects.create_user(
            username="reviewer",
            password="not-a-production-password",
        )
        excerpt = EvidenceExcerpt.objects.create(
            source=self.source,
            text="Minimal evidence excerpt.",
            locator="Section 1",
        )
        decision = ReviewDecision.objects.create(
            candidate=candidate,
            reviewer=reviewer,
            action=ReviewDecision.Action.NEEDS_EVIDENCE,
            notes=f"Review the evidence excerpt {excerpt.id}.",
        )

        self.assertEqual(decision.reviewer, reviewer)
        self.assertEqual(decision.action, ReviewDecision.Action.NEEDS_EVIDENCE)

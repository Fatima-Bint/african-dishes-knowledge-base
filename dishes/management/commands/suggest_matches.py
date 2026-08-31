from difflib import SequenceMatcher

from django.core.management.base import BaseCommand, CommandError

from dishes.models import CandidateMatch, CandidateRecord, Dish, DishName
from dishes.services import normalize_name


class Command(BaseCommand):
    help = "Generate deterministic name-match suggestions for an extracted candidate."

    def add_arguments(self, parser):
        parser.add_argument("candidate_id")
        parser.add_argument("--limit", type=int, default=5)

    def handle(self, *args, **options):
        try:
            candidate = CandidateRecord.objects.get(id=options["candidate_id"])
        except CandidateRecord.DoesNotExist as exc:
            raise CommandError("Candidate record was not found.") from exc

        payload = candidate.extracted_payload or {}
        candidate_name = payload.get("candidate_name")
        if not candidate_name:
            raise CommandError("The candidate has no schema-valid candidate_name.")

        normalized_candidate = normalize_name(candidate_name)
        scored = []
        for name in DishName.objects.select_related("dish").all():
            score = SequenceMatcher(
                None, normalized_candidate, name.normalized_name
            ).ratio()
            if score >= 0.55:
                scored.append((score, name.dish))

        unique_dishes = {}
        for score, dish in sorted(scored, key=lambda item: item[0], reverse=True):
            unique_dishes.setdefault(dish.id, (score, dish))

        CandidateMatch.objects.filter(candidate=candidate).delete()
        suggestions = list(unique_dishes.values())[: max(1, options["limit"])]
        for score, dish in suggestions:
            decision = (
                CandidateMatch.ProposedDecision.SAME_DISH
                if score == 1
                else CandidateMatch.ProposedDecision.UNCERTAIN
            )
            CandidateMatch.objects.create(
                candidate=candidate,
                proposed_dish=dish,
                proposed_decision=decision,
                deterministic_score=score,
                rationale="Deterministic comparison of normalized canonical and alternative names.",
            )

        if not suggestions:
            CandidateMatch.objects.create(
                candidate=candidate,
                proposed_dish=None,
                proposed_decision=CandidateMatch.ProposedDecision.NEW_DISH,
                deterministic_score=0,
                rationale="No normalized name exceeded the deterministic similarity threshold.",
            )

        candidate.processing_status = CandidateRecord.ProcessingStatus.MATCHED
        candidate.save(update_fields=["processing_status", "updated_at"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {max(1, len(suggestions))} match suggestion(s)."
            )
        )
        self.stdout.write("Next: inspect the candidate, evidence and matches in Admin.")

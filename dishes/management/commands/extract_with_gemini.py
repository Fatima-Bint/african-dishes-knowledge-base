import json
import os

from django.core.management.base import BaseCommand, CommandError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from dishes.models import CandidateRecord


class EvidenceValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str | None = None
    evidence: str | None = None


class AlternativeName(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    language_code: str | None = None
    evidence: str


class LocationClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location_name: str
    relationship: str
    evidence: str


class IngredientMention(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    evidence: str


class CandidatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_name: str
    description: EvidenceValue
    alternative_names: list[AlternativeName] = Field(default_factory=list)
    location_claims: list[LocationClaim] = Field(default_factory=list)
    category: EvidenceValue
    ingredient_mentions: list[IngredientMention] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    unsupported_or_missing_fields: list[str] = Field(default_factory=list)


SYSTEM_RULES = """
You extract reviewable claims about one African dish from a supplied source excerpt.
Use only the excerpt. Never use background knowledge. Copy the minimum exact evidence
text for every proposed claim. Use null or an empty list when the excerpt does not
support a field. Do not infer exclusive origin from cultural association. Record
ambiguity explicitly. Return only schema-valid JSON.
""".strip()


class Command(BaseCommand):
    help = "Extract one schema-validated candidate from a stored source using Gemini."

    def add_arguments(self, parser):
        parser.add_argument("candidate_id")
        parser.add_argument("--model", default=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

    def handle(self, *args, **options):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise CommandError("GEMINI_API_KEY is not configured.")

        try:
            candidate = CandidateRecord.objects.select_related("source").get(
                id=options["candidate_id"]
            )
        except CandidateRecord.DoesNotExist as exc:
            raise CommandError("Candidate record was not found.") from exc

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=options["model"],
                contents=(
                    f"{SYSTEM_RULES}\n\n"
                    f"SOURCE TITLE: {candidate.source.title}\n"
                    f"SOURCE EXCERPT:\n{candidate.submitted_text}"
                ),
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type="application/json",
                    response_schema=CandidatePayload,
                ),
            )
            raw_response = response.text or ""
            payload = CandidatePayload.model_validate_json(raw_response)
        except (ValidationError, json.JSONDecodeError) as exc:
            candidate.raw_model_response = locals().get("raw_response", "")
            candidate.validation_errors = [str(exc)]
            candidate.extraction_model = options["model"]
            candidate.prompt_version = "candidate-extraction-v1"
            candidate.processing_status = CandidateRecord.ProcessingStatus.INVALID
            candidate.save()
            raise CommandError("Gemini returned output that failed schema validation.") from exc
        except Exception as exc:
            raise CommandError(f"Gemini extraction failed: {exc}") from exc

        candidate.raw_model_response = raw_response
        candidate.extracted_payload = payload.model_dump(mode="json")
        candidate.validation_errors = []
        candidate.extraction_model = options["model"]
        candidate.prompt_version = "candidate-extraction-v1"
        candidate.processing_status = CandidateRecord.ProcessingStatus.EXTRACTED
        candidate.save()

        self.stdout.write(self.style.SUCCESS("Schema-valid candidate extracted."))
        self.stdout.write(f"Candidate: {candidate.id}")
        self.stdout.write(f"Proposed name: {payload.candidate_name}")
        self.stdout.write("Next: run suggest_matches, then review the candidate in Admin.")

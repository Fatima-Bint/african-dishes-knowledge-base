import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils.text import slugify


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ReviewStatus(models.TextChoices):
    EXTRACTED = "extracted", "Extracted"
    NEEDS_EVIDENCE = "needs_evidence", "Needs evidence"
    REVIEWED = "reviewed", "Reviewed"
    CORROBORATED = "corroborated", "Corroborated"
    CONTESTED = "contested", "Contested"
    REJECTED = "rejected", "Rejected"


class Location(TimestampedModel):
    class LocationType(models.TextChoices):
        CONTINENT = "continent", "Continent"
        COUNTRY = "country", "Country"
        REGION = "region", "Region"
        LOCALITY = "locality", "Locality"
        COMMUNITY = "community", "Community"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    location_type = models.CharField(max_length=20, choices=LocationType.choices)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )
    iso_code = models.CharField(max_length=12, blank=True)
    wikidata_id = models.CharField(max_length=24, null=True, blank=True, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "location_type", "parent"],
                name="unique_location_within_parent",
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name


class DishCategory(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Dish(TimestampedModel):
    class PublicationStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEW = "review", "In review"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    canonical_name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        DishCategory,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="dishes",
    )
    publication_status = models.CharField(
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.canonical_name) or str(self.id)
            self.slug = base_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.canonical_name


class DishName(TimestampedModel):
    class NameType(models.TextChoices):
        CANONICAL = "canonical", "Canonical"
        ALTERNATIVE = "alternative", "Alternative"
        LOCAL = "local", "Local"
        HISTORICAL = "historical", "Historical"
        ABBREVIATION = "abbreviation", "Abbreviation"

    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name="names")
    name = models.CharField(max_length=200)
    normalized_name = models.CharField(max_length=200, db_index=True)
    language_code = models.CharField(max_length=20, blank=True)
    script = models.CharField(max_length=50, blank=True)
    name_type = models.CharField(max_length=20, choices=NameType.choices)
    is_preferred = models.BooleanField(default=False)
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.EXTRACTED,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dish", "normalized_name", "language_code", "name_type"],
                name="unique_dish_name_form",
            )
        ]

    def __str__(self):
        return self.name


class DishLocation(TimestampedModel):
    class Relationship(models.TextChoices):
        ASSOCIATED_WITH = "associated_with", "Associated with"
        DOCUMENTED_IN = "documented_in", "Documented in"
        COMMONLY_CONSUMED_IN = "commonly_consumed_in", "Commonly consumed in"
        CLAIMED_ORIGIN = "claimed_origin", "Claimed origin"
        SHARED_ACROSS = "shared_across", "Shared across"
        UNCERTAIN = "uncertain", "Uncertain"

    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name="locations")
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="dish_associations",
    )
    relationship = models.CharField(max_length=30, choices=Relationship.choices)
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.EXTRACTED,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dish", "location", "relationship"],
                name="unique_dish_location_relationship",
            )
        ]


class DishRelationship(TimestampedModel):
    class RelationshipType(models.TextChoices):
        VARIANT_OF = "variant_of", "Variant of"
        RELATED_TO = "related_to", "Related to"
        SERVED_WITH = "served_with", "Served with"
        DERIVED_FROM = "derived_from", "Derived from"
        UNCERTAIN = "uncertain", "Uncertain relationship"

    source_dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
    )
    target_dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
    )
    relationship_type = models.CharField(max_length=24, choices=RelationshipType.choices)
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.EXTRACTED,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(source_dish=F("target_dish")),
                name="prevent_self_dish_relationship",
            ),
            models.UniqueConstraint(
                fields=["source_dish", "target_dish", "relationship_type"],
                name="unique_dish_relationship",
            ),
        ]


class Source(TimestampedModel):
    class SourceType(models.TextChoices):
        ACADEMIC = "academic", "Academic"
        GOVERNMENT = "government", "Government"
        INSTITUTIONAL = "institutional", "Institutional"
        WIKIDATA = "wikidata", "Wikidata"
        WIKIPEDIA = "wikipedia", "Wikipedia"
        BOOK = "book", "Book"
        COMMUNITY = "community", "Community"
        CULINARY = "culinary", "Culinary publication"
        OTHER = "other", "Other"

    class SourceTier(models.TextChoices):
        A = "A", "Tier A"
        B = "B", "Tier B"
        C = "C", "Tier C"
        D = "D", "Tier D — discovery only"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, blank=True)
    stable_identifier = models.CharField(max_length=255, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    author = models.CharField(max_length=255, blank=True)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    source_tier = models.CharField(max_length=1, choices=SourceTier.choices)
    publication_date = models.DateField(null=True, blank=True)
    retrieved_at = models.DateTimeField()
    licence_name = models.CharField(max_length=120, blank=True)
    licence_url = models.URLField(max_length=1000, blank=True)
    citation_text = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.title


class EvidenceExcerpt(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="excerpts")
    text = models.TextField()
    locator = models.CharField(max_length=255, blank=True)
    language_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.source}: {self.locator or 'excerpt'}"


class DishClaim(TimestampedModel):
    class ClaimType(models.TextChoices):
        DESCRIPTION = "description", "Description"
        NAME_EQUIVALENCE = "name_equivalence", "Name equivalence"
        LOCATION = "location", "Location association"
        CATEGORY = "category", "Category"
        INGREDIENT_MENTION = "ingredient_mention", "Ingredient mention"
        RELATIONSHIP = "relationship", "Dish relationship"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name="claims")
    claim_type = models.CharField(max_length=30, choices=ClaimType.choices)
    value = models.JSONField()
    evidence = models.ManyToManyField(EvidenceExcerpt, related_name="claims")
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.EXTRACTED,
    )
    reviewer_note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.dish}: {self.claim_type}"


class CandidateRecord(TimestampedModel):
    class ProcessingStatus(models.TextChoices):
        RECEIVED = "received", "Received"
        EXTRACTED = "extracted", "Extracted"
        INVALID = "invalid", "Invalid model output"
        MATCHED = "matched", "Potential matches generated"
        IN_REVIEW = "in_review", "In review"
        DECIDED = "decided", "Decision recorded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="candidates")
    submitted_text = models.TextField()
    extraction_model = models.CharField(max_length=120, blank=True)
    prompt_version = models.CharField(max_length=40, blank=True)
    raw_model_response = models.TextField(blank=True)
    extracted_payload = models.JSONField(null=True, blank=True)
    validation_errors = models.JSONField(default=list, blank=True)
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.RECEIVED,
        db_index=True,
    )

    def __str__(self):
        return f"Candidate {self.id} from {self.source}"


class CandidateMatch(TimestampedModel):
    class ProposedDecision(models.TextChoices):
        NEW_DISH = "new_dish", "New dish"
        SAME_DISH = "same_dish", "Same dish"
        REGIONAL_VARIANT = "regional_variant", "Regional variant"
        RELATED_DISH = "related_dish", "Related dish"
        UNCERTAIN = "uncertain", "Uncertain"

    candidate = models.ForeignKey(
        CandidateRecord,
        on_delete=models.CASCADE,
        related_name="match_suggestions",
    )
    proposed_dish = models.ForeignKey(
        Dish,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="candidate_matches",
    )
    proposed_decision = models.CharField(max_length=24, choices=ProposedDecision.choices)
    deterministic_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    model_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    model_identifier = models.CharField(max_length=120, blank=True)
    rationale = models.TextField(blank=True)
    evidence_summary = models.JSONField(default=list, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "proposed_dish", "proposed_decision"],
                name="unique_candidate_match_suggestion",
            )
        ]


class ReviewDecision(TimestampedModel):
    class Action(models.TextChoices):
        APPROVE_NEW = "approve_new", "Approve as new dish"
        LINK_EXISTING = "link_existing", "Link to existing dish"
        APPROVE_VARIANT = "approve_variant", "Approve as variant"
        APPROVE_RELATED = "approve_related", "Approve as related"
        EDIT_APPROVE = "edit_approve", "Edit and approve"
        REJECT = "reject", "Reject"
        NEEDS_EVIDENCE = "needs_evidence", "Needs more evidence"

    candidate = models.ForeignKey(
        CandidateRecord,
        on_delete=models.PROTECT,
        related_name="review_decisions",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="dish_review_decisions",
    )
    action = models.CharField(max_length=24, choices=Action.choices)
    resulting_dish = models.ForeignKey(
        Dish,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="review_decisions",
    )
    notes = models.TextField(blank=True)
    corrected_payload = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.action} for {self.candidate_id}"

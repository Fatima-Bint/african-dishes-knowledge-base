import copy

from django import forms

from .category_data import CONTROLLED_CATEGORIES
from .models import CandidateRecord, DishCategory, DishLocation, Location


def _payload_value(payload, key):
    value = payload.get(key)
    if isinstance(value, dict):
        return value.get("value") or ""
    return value or ""


def _payload_alternatives(payload):
    names = []
    for item in payload.get("alternative_names") or []:
        if isinstance(item, dict):
            value = item.get("name") or item.get("value")
        else:
            value = item
        if value:
            names.append(str(value).strip())
    return names


class CandidateRecordReviewForm(forms.ModelForm):
    """Expose safe, human-readable proposal fields in Django Admin."""

    candidate_name = forms.CharField(
        label="Proposed canonical name",
        max_length=200,
        help_text="Edit this value before approval if the imported label is not the preferred public name.",
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea,
        help_text="Use only what the evidence supports.",
    )
    category = forms.ChoiceField(
        choices=(),
        required=False,
        help_text="Choose a predefined category. Add categories in Admin only.",
    )
    location = forms.ModelChoiceField(
        queryset=Location.objects.none(),
        required=False,
        empty_label="— Not established —",
        help_text="Choose an existing country, region, locality or community.",
    )
    location_relationship = forms.ChoiceField(
        choices=[("", "— Not established —")] + list(DishLocation.Relationship.choices),
        required=False,
        label="Location relationship",
        help_text="Use 'claimed origin' only when the evidence supports that wording.",
    )
    image_url = forms.URLField(
        required=False,
        label="Proposed image URL",
        help_text="Optional. Publish only images with a clear source and reuse permission.",
    )
    image_caption = forms.CharField(required=False, max_length=300)
    image_credit = forms.CharField(required=False, max_length=255)
    image_license = forms.CharField(required=False, max_length=120)
    image_source_url = forms.URLField(required=False, label="Image source URL")
    alternative_names = forms.CharField(
        required=False,
        widget=forms.TextInput,
        help_text="Comma-separated names; remove aliases that are not confirmed.",
    )

    class Meta:
        model = CandidateRecord
        fields = ("processing_status",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].choices = [("", "— Not established —")] + [
            (name, name) for name in CONTROLLED_CATEGORIES
        ]
        self.fields["location"].queryset = Location.objects.order_by("name")
        payload = self.instance.extracted_payload or {}
        self.fields["candidate_name"].initial = payload.get("candidate_name", "")
        self.fields["description"].initial = _payload_value(payload, "description")
        self.fields["category"].initial = _payload_value(payload, "category")
        self.fields["location"].initial = Location.objects.filter(
            name=_payload_value(payload, "location")
        ).first()
        self.fields["location_relationship"].initial = payload.get(
            "location_relationship", "associated_with"
        )
        image = payload.get("image") or {}
        self.fields["image_url"].initial = image.get("url", "")
        self.fields["image_caption"].initial = image.get("caption", "")
        self.fields["image_credit"].initial = image.get("credit", "")
        self.fields["image_license"].initial = image.get("license", "")
        self.fields["image_source_url"].initial = image.get("source_url", "")
        self.fields["alternative_names"].initial = ", ".join(
            _payload_alternatives(payload)
        )

    def save(self, commit=True):
        candidate = super().save(commit=False)
        payload = copy.deepcopy(candidate.extracted_payload or {})
        original_description = payload.get("description")
        original_category = payload.get("category")
        payload["candidate_name"] = self.cleaned_data["candidate_name"].strip()
        payload["description"] = {
            "value": self.cleaned_data["description"].strip(),
            "evidence": (
                original_description.get("evidence", "")
                if isinstance(original_description, dict)
                else ""
            ),
        }
        category = self.cleaned_data["category"].strip()
        payload["category"] = {
            "value": category,
            "evidence": (
                original_category.get("evidence", "")
                if isinstance(original_category, dict)
                else ""
            ),
        }
        payload["alternative_names"] = [
            {"name": name.strip(), "language_code": "en"}
            for name in self.cleaned_data["alternative_names"].split(",")
            if name.strip()
        ]
        location = self.cleaned_data["location"]
        payload["location"] = location.name if location else ""
        payload["location_relationship"] = self.cleaned_data["location_relationship"]
        payload["image"] = {
            "url": self.cleaned_data["image_url"].strip(),
            "caption": self.cleaned_data["image_caption"].strip(),
            "credit": self.cleaned_data["image_credit"].strip(),
            "license": self.cleaned_data["image_license"].strip(),
            "source_url": self.cleaned_data["image_source_url"].strip(),
        }
        candidate.extracted_payload = payload
        if commit:
            candidate.save()
        return candidate

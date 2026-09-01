import copy

from django import forms

from .models import CandidateRecord


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
    category = forms.CharField(
        required=False,
        max_length=100,
        help_text="Leave blank when the category is not established.",
    )
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
        payload = self.instance.extracted_payload or {}
        self.fields["candidate_name"].initial = payload.get("candidate_name", "")
        self.fields["description"].initial = _payload_value(payload, "description")
        self.fields["category"].initial = _payload_value(payload, "category")
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
        payload["category"] = {
            "value": self.cleaned_data["category"].strip(),
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
        candidate.extracted_payload = payload
        if commit:
            candidate.save()
        return candidate

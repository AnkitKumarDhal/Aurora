from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class InterviewExtraction(BaseModel):
    """
    Small, strict contract returned by the interview LLM.

    The LLM extracts facts from the patient's latest answer.
    It does not decide the next question.
    """

    topic: str | None = None
    fields: dict[str, Any] = Field(default_factory=dict)
    negatives: list[str] = Field(default_factory=list)


INTERVIEW_FIELD_ALIASES: dict[str, str] = {
    "complaint": "chief_complaint",
    "main_complaint": "chief_complaint",
    "problem": "chief_complaint",
    "symptom": "chief_complaint",

    "duration": "onset",
    "started": "onset",
    "start": "onset",
    "when_started": "onset",

    "location": "site",
    "place": "site",
    "where": "site",

    "pain_score": "severity",
    "pain_level": "severity",
    "intensity": "severity",

    "pain_type": "character",
    "quality": "character",

    "frequency": "timing",
    "pattern": "timing",

    "worse_with": "aggravating_factors",
    "aggravated_by": "aggravating_factors",

    "better_with": "relieving_factors",
    "relieved_by": "relieving_factors",

    "radiates_to": "radiation",

    "associated": "associated_symptoms",
    "other_symptoms": "associated_symptoms",

    "breathlessness": "breathing_difficulty",
    "shortness_of_breath": "breathing_difficulty",

    "nausea": "nausea_vomiting",
    "vomiting": "nausea_vomiting",
    "nausea_or_vomiting": "nausea_vomiting",

    "vision": "vision_or_neuro",
    "neurological_symptoms": "vision_or_neuro",

    "coughing": "cough",
    "wheezing": "wheeze",

    "burning_urination": "urinary_burning",
    "painful_urination": "urinary_burning",

    "blood_in_urine": "urinary_blood",

    "rash_location": "site",
    "rash_appearance": "appearance",
    "itching": "itch_or_pain",

    "fever": "fever",
    "fatigue": "fatigue",
    "weight_change": "weight_change",

    "past_history": "past_medical_history",
    "medical_history": "past_medical_history",

    "current_medications": "medications",
    "drugs": "medications",

    "drug_allergies": "allergies",
}


KNOWN_INTERVIEW_FIELDS = {
    "chief_complaint",
    "onset",
    "site",
    "severity",
    "character",
    "timing",
    "aggravating_factors",
    "relieving_factors",
    "radiation",
    "associated_symptoms",
    "breathing_difficulty",
    "nausea_vomiting",
    "vision_or_neuro",
    "cough",
    "wheeze",
    "location",
    "bowel_changes",
    "appearance",
    "itch_or_pain",
    "spread",
    "urinary_frequency",
    "urinary_burning",
    "urinary_blood",
    "fever",
    "fatigue",
    "weight_change",
    "past_medical_history",
    "medications",
    "allergies",
}


def normalize_field_name(name: str) -> str | None:
    key = str(name).strip().lower().replace("-", "_").replace(" ", "_")

    if key in KNOWN_INTERVIEW_FIELDS:
        return key

    return INTERVIEW_FIELD_ALIASES.get(key)

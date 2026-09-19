from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field, model_validator


class InterviewExtraction(BaseModel):
    topic: str | None = None
    fields: dict[str, Any] = Field(default_factory=dict)
    negatives: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def infer_missing_topic(self) -> "InterviewExtraction":
        if self.topic not in {None, "", "general"}:
            return self

        values = " ".join(
            str(value)
            for value in self.fields.values()
            if value is not None
        ).lower()

        topic_keywords = {
            "headache": (
                "headache",
                "head pain",
                "migraine",
            ),
            "chest_pain": (
                "chest pain",
                "chest pressure",
                "chest discomfort",
            ),
            "respiratory": (
                "shortness of breath",
                "breathlessness",
                "breathing problem",
                "difficulty breathing",
                "cough",
                "wheezing",
                "wheeze",
            ),
            "gastrointestinal": (
                "stomach pain",
                "abdominal pain",
                "abdomen",
                "diarrhea",
                "vomiting",
                "nausea",
            ),
            "skin": (
                "rash",
                "itching",
                "skin",
            ),
            "urinary": (
                "urine",
                "urination",
                "burning while urinating",
            ),
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in values for keyword in keywords):
                self.topic = topic
                return self

        return self


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

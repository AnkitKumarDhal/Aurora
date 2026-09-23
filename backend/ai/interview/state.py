from __future__ import annotations

import json
import re
from typing import Any


STATE_SIGNAL_NAME = "_interview_state"

SECTION_ORDER = (
    "hpi",
    "past_history",
    "drug_allergy",
    "family_history",
    "personal_history",
    "review_of_systems",
)

REQUIRED_SECTIONS = set(SECTION_ORDER)

HISTORY_FIELDS = {
    "past_medical_history",
    "past_surgical_history",
    "hospitalizations",
    "immunizations",
    "medications",
    "allergies",
    "adverse_drug_reactions",
    "family_history",
    "personal_history",
    "occupation",
    "diet",
    "sleep",
    "physical_activity",
    "smoking",
    "alcohol",
    "tobacco",
    "menstrual_history",
    "pregnancy_status",
    "sexual_history",
    "review_of_systems",
}

HPI_FIELDS = {
    "chief_complaint",
    "onset",
    "course",
    "duration",
    "site",
    "laterality",
    "severity",
    "character",
    "timing",
    "frequency",
    "aggravating_factors",
    "relieving_factors",
    "radiation",
    "associated_symptoms",
    "previous_episodes",
    "impact_on_daily_life",
    "prior_treatment",
    "response_to_treatment",
    "prior_investigations",
    "constitutional",
    "cardiovascular",
    "respiratory",
    "gastrointestinal",
    "genitourinary",
    "neurological",
    "musculoskeletal",
    "skin",
    "endocrine",
    "hematologic",
    "psychiatric",
    "breathing_difficulty",
    "nausea_vomiting",
    "vision_or_neuro",
    "cough",
    "wheeze",
    "fever",
    "fatigue",
    "weight_change",
    "bowel_changes",
    "bowel_frequency",
    "stool_consistency",
    "straining",
    "blood_in_stool",
    "abdominal_distension",
    "urinary_frequency",
    "urinary_burning",
    "urinary_blood",
}

AYUSH_FIELDS = {
    "ayush_prakriti",
    "ayush_vikriti",
    "ayush_sara",
    "ayush_samhanana",
    "ayush_pramana",
    "ayush_satmya",
    "ayush_satva",
    "ayush_ahara_shakti",
    "ayush_vyayama_shakti",
    "ayush_vaya",
    "ayush_agni",
    "ayush_koshta",
    "ayush_ahara_vihara",
    "ayush_nidana",
    "ayush_samprapti",
}

KNOWN_FIELDS = HPI_FIELDS | HISTORY_FIELDS | AYUSH_FIELDS

FIELD_ALIASES = {
    "complaint": "chief_complaint",
    "main_complaint": "chief_complaint",
    "main_problem": "chief_complaint",
    "problem": "chief_complaint",
    "symptom": "chief_complaint",
    "started": "onset",
    "start": "onset",
    "when_started": "onset",
    "how_long": "duration",
    "progression": "course",
    "pattern": "timing",
    "pain_score": "severity",
    "pain_level": "severity",
    "intensity": "severity",
    "pain_type": "character",
    "quality": "character",
    "location": "site",
    "where": "site",
    "place": "site",
    "side": "laterality",
    "worse_with": "aggravating_factors",
    "aggravated_by": "aggravating_factors",
    "better_with": "relieving_factors",
    "relieved_by": "relieving_factors",
    "radiates_to": "radiation",
    "associated": "associated_symptoms",
    "other_symptoms": "associated_symptoms",
    "family": "family_history",
    "social_history": "personal_history",
    "lifestyle": "personal_history",
    "occupation_history": "occupation",
    "smoking_history": "smoking",
    "tobacco_use": "tobacco",
    "alcohol_use": "alcohol",
    "exercise": "physical_activity",
    "diet_history": "diet",
    "sleep_history": "sleep",
    "ros": "review_of_systems",
    "review_of_system": "review_of_systems",
    "medical_history": "past_medical_history",
    "past_history": "past_medical_history",
    "surgical_history": "past_surgical_history",
    "surgery_history": "past_surgical_history",
    "operations": "past_surgical_history",
    "hospital_history": "hospitalizations",
    "current_medications": "medications",
    "drugs": "medications",
    "drug_history": "medications",
    "drug_allergies": "allergies",
    "medicine_allergies": "allergies",
    "adverse_reactions": "adverse_drug_reactions",
    "investigations": "prior_investigations",
    "previous_tests": "prior_investigations",
    "prior_tests": "prior_investigations",
    "treatment_history": "prior_treatment",
    "treatment_response": "response_to_treatment",
    "breathlessness": "breathing_difficulty",
    "shortness_of_breath": "breathing_difficulty",
    "difficulty_breathing": "breathing_difficulty",
    "nausea": "nausea_vomiting",
    "vomiting": "nausea_vomiting",
    "nausea_or_vomiting": "nausea_vomiting",
    "vision": "vision_or_neuro",
    "neurological_symptoms": "vision_or_neuro",
    "coughing": "cough",
    "wheezing": "wheeze",
    "itching": "skin",
    "painful_urination": "urinary_burning",
    "burning_urination": "urinary_burning",
    "blood_in_urine": "urinary_blood",
    "rectal_bleeding": "blood_in_stool",
    "blood_in_stools": "blood_in_stool",
    "bowel_problem": "bowel_changes",
    "constipation": "bowel_changes",
    "constipated": "bowel_changes",
    "stool_frequency": "bowel_frequency",
    "stool_type": "stool_consistency",
    "abdominal_bloating": "abdominal_distension",
    "bloating": "abdominal_distension",
    "menstrual": "menstrual_history",
    "periods": "menstrual_history",
    "sexual": "sexual_history",
    "prakriti": "ayush_prakriti",
    "vikriti": "ayush_vikriti",
    "sara": "ayush_sara",
    "samhanana": "ayush_samhanana",
    "pramana": "ayush_pramana",
    "satmya": "ayush_satmya",
    "satva": "ayush_satva",
    "ahara_shakti": "ayush_ahara_shakti",
    "vyayama_shakti": "ayush_vyayama_shakti",
    "vaya": "ayush_vaya",
    "agni": "ayush_agni",
    "koshta": "ayush_koshta",
    "ahara_vihara": "ayush_ahara_vihara",
    "nidana": "ayush_nidana",
    "samprapti": "ayush_samprapti",
}

FIELD_PRIMARY_SECTION = {
    **{field: "hpi" for field in HPI_FIELDS},
    **{
        field: "past_history"
        for field in HISTORY_FIELDS
        if field
        in {
            "past_medical_history",
            "past_surgical_history",
            "hospitalizations",
            "immunizations",
        }
    },
    **{
        field: "drug_allergy"
        for field in {
            "medications",
            "allergies",
            "adverse_drug_reactions",
        }
    },
    "family_history": "family_history",
    **{
        field: "personal_history"
        for field in {
            "personal_history",
            "occupation",
            "diet",
            "sleep",
            "physical_activity",
            "smoking",
            "alcohol",
            "tobacco",
            "menstrual_history",
            "pregnancy_status",
            "sexual_history",
        }
    },
    "review_of_systems": "review_of_systems",
    **{field: "ayush" for field in AYUSH_FIELDS},
}

MULTI_VALUE_FIELDS = {
    "past_medical_history",
    "past_surgical_history",
    "hospitalizations",
    "immunizations",
    "medications",
    "allergies",
    "adverse_drug_reactions",
    "family_history",
    "personal_history",
    "associated_symptoms",
    "prior_treatment",
    "prior_investigations",
    "review_of_systems",
    "aggravating_factors",
    "relieving_factors",
    "radiation",
}


def normalize_section(
    section: str | None,
) -> str:
    value = (
        str(section or "hpi")
        .strip()
        .lower()
        .replace("-", "_")
    )

    if value == "medical_history":
        return "past_history"

    if value == "drug_history":
        return "drug_allergy"

    if value not in {
        *SECTION_ORDER,
        "ayush",
    }:
        return "hpi"

    return value


def normalize_field_name(
    name: str | None,
) -> str:
    value = (
        str(name or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    if value in KNOWN_FIELDS:
        return value

    return (
        FIELD_ALIASES.get(value)
        or f"custom_{slugify(value)}"
    )


def slugify(
    value: str,
) -> str:
    result = re.sub(
        r"[^a-z0-9_]+",
        "_",
        value.lower(),
    ).strip("_")

    return result[:80] or "fact"


def _clean_value(
    value: Any,
) -> Any:
    if isinstance(value, str):
        return " ".join(
            value.strip().split()
        )

    if isinstance(value, list):
        cleaned = [
            _clean_value(item)
            for item in value
        ]

        return [
            item
            for item in cleaned
            if item not in (None, "")
        ]

    if isinstance(value, dict):
        return {
            str(key): _clean_value(item)
            for key, item in value.items()
        }

    return value


def _value_key(
    value: Any,
) -> str:
    return json.dumps(
        _clean_value(value),
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    ).lower()


class InterviewState:
    def __init__(
        self,
        topic: str = "general",
        current_section: str = "hpi",
        completed_sections: set[str] | None = None,
        facts: list[dict[str, Any]] | None = None,
        question_history: list[str] | None = None,
    ) -> None:
        self.topic = topic or "general"
        self.current_section = normalize_section(
            current_section
        )
        self.completed_sections = set(
            completed_sections or set()
        )
        self.facts = list(
            facts or []
        )
        self.question_history = list(
            question_history or []
        )

    @classmethod
    def empty(
        cls,
    ) -> "InterviewState":
        return cls()

    @classmethod
    def from_value(
        cls,
        value: Any,
        legacy_fields: dict[str, Any] | None = None,
    ) -> "InterviewState":
        if isinstance(
            value,
            str,
        ):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = None

        if isinstance(
            value,
            dict,
        ):
            return cls(
                topic=str(
                    value.get("topic")
                    or "general"
                ),
                current_section=str(
                    value.get(
                        "current_section"
                    )
                    or "hpi"
                ),
                completed_sections={
                    normalize_section(item)
                    for item in value.get(
                        "completed_sections",
                        [],
                    )
                    if normalize_section(item)
                    in {
                        *SECTION_ORDER,
                        "ayush",
                    }
                },
                facts=value.get(
                    "facts",
                    [],
                ),
                question_history=[
                    str(item).strip()
                    for item in value.get(
                        "question_history",
                        [],
                    )
                    if str(item).strip()
                ],
            )

        state = cls.empty()

        if not legacy_fields:
            return state

        section = normalize_section(
            legacy_fields.get(
                "_interview_section"
            )
        )

        completed = legacy_fields.get(
            "_interview_completed_sections"
        )

        if isinstance(
            completed,
            str,
        ):
            try:
                completed = json.loads(
                    completed
                )
            except json.JSONDecodeError:
                completed = completed.split(",")

        if isinstance(
            completed,
            list,
        ):
            state.mark_sections(
                completed
            )

        state.current_section = section

        for field, value_item in legacy_fields.items():
            if field.startswith("_"):
                continue

            if field == "symptom_topic":
                continue

            state.add_fact(
                section=FIELD_PRIMARY_SECTION.get(
                    field,
                    section,
                ),
                field=field,
                value=value_item,
                evidence=None,
                turn_id=None,
            )

        return state

    def to_value(
        self,
    ) -> str:
        return json.dumps(
            {
                "topic": self.topic,
                "current_section": self.current_section,
                "completed_sections": sorted(
                    self.completed_sections
                ),
                "facts": self.facts[-250:],
                "question_history": (
                    self.question_history[-30:]
                ),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def add_fact(
        self,
        section: str,
        field: str,
        value: Any,
        evidence: str | None,
        turn_id: str | None,
        negative: bool = False,
    ) -> None:
        normalized_section = normalize_section(
            section
        )
        normalized_field = normalize_field_name(
            field
        )
        cleaned_value = _clean_value(
            value
        )

        if cleaned_value in (
            None,
            "",
            [],
        ):
            return

        boolean_placeholder = (
            cleaned_value is True
            or cleaned_value == [True]
            or cleaned_value == ["true"]
        )

        if (
            normalized_field
            in MULTI_VALUE_FIELDS
            and not boolean_placeholder
            and not negative
        ):
            self.facts = [
                item
                for item in self.facts
                if not (
                    item.get("field")
                    == normalized_field
                    and item.get("value")
                    is True
                    and not item.get("negative")
                )
            ]

        fact = {
            "section": normalized_section,
            "field": normalized_field,
            "value": cleaned_value,
            "negative": negative,
            "evidence": evidence,
            "turn_id": turn_id,
        }

        key = (
            normalized_section,
            normalized_field,
            _value_key(
                cleaned_value
            ),
            negative,
        )

        existing_keys = {
            (
                item.get("section"),
                item.get("field"),
                _value_key(
                    item.get("value")
                ),
                bool(
                    item.get(
                        "negative"
                    )
                ),
            )
            for item in self.facts
        }

        if key not in existing_keys:
            self.facts.append(
                fact
            )

    def add_facts(
        self,
        facts: list[dict[str, Any]],
        evidence: str | None,
        turn_id: str | None,
    ) -> None:
        for fact in facts:
            if not isinstance(
                fact,
                dict,
            ):
                continue

            self.add_fact(
                section=str(
                    fact.get(
                        "section"
                    )
                    or self.current_section
                ),
                field=str(
                    fact.get(
                        "field"
                    )
                    or ""
                ),
                value=fact.get(
                    "value"
                ),
                evidence=str(
                    fact.get(
                        "evidence"
                    )
                    or evidence
                    or ""
                ).strip()
                or None,
                turn_id=turn_id,
                negative=bool(
                    fact.get(
                        "negative",
                        False,
                    )
                ),
            )

    def add_negative(
        self,
        section: str,
        field: str,
        evidence: str | None,
        turn_id: str | None,
    ) -> None:
        self.add_fact(
            section=section,
            field=field,
            value=False,
            evidence=evidence,
            turn_id=turn_id,
            negative=True,
        )

    def add_question(
        self,
        question: str | None,
    ) -> None:
        if not question:
            return

        value = " ".join(
            question.strip().split()
        )

        if not value:
            return

        if (
            not self.question_history
            or self.question_history[-1].lower()
            != value.lower()
        ):
            self.question_history.append(
                value
            )

    def mark_sections(
        self,
        sections: list[str] | set[str] | None,
    ) -> None:
        for section in sections or []:
            normalized = normalize_section(
                section
            )

            if normalized in {
                *SECTION_ORDER,
                "ayush",
            }:
                self.completed_sections.add(
                    normalized
                )

    def known_fields(
        self,
    ) -> dict[str, Any]:
        grouped: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for fact in self.facts:
            grouped.setdefault(
                fact.get(
                    "field",
                    "",
                ),
                [],
            ).append(fact)

        result: dict[str, Any] = {}

        for field, facts in grouped.items():
            if not field:
                continue

            positives = [
                item.get(
                    "value"
                )
                for item in facts
                if not item.get(
                    "negative"
                )
            ]

            negatives = [
                item.get(
                    "value"
                )
                for item in facts
                if item.get(
                    "negative"
                )
            ]

            if positives:
                if field in MULTI_VALUE_FIELDS:
                    values: list[str] = []

                    for value in positives:
                        for item in (
                            value
                            if isinstance(
                                value,
                                list,
                            )
                            else [value]
                        ):
                            text = str(
                                item
                            ).strip()

                            if (
                                text
                                and text not in values
                            ):
                                values.append(
                                    text
                                )

                    result[field] = (
                        values
                        if len(values) > 1
                        else values[0]
                        if values
                        else None
                    )
                else:
                    result[field] = (
                        positives[-1]
                    )
            elif negatives:
                result[field] = False

        return {
            key: value
            for key, value in result.items()
            if value is not None
        }

    def section_facts(
        self,
        section: str,
    ) -> list[dict[str, Any]]:
        normalized = normalize_section(
            section
        )

        return [
            fact
            for fact in self.facts
            if normalize_section(
                fact.get(
                    "section"
                )
            )
            == normalized
        ]

    def section_summary(
        self,
    ) -> dict[str, dict[str, Any]]:
        result: dict[
            str,
            dict[str, Any],
        ] = {}

        for section in (
            *SECTION_ORDER,
            "ayush",
        ):
            result[section] = {
                "completed": (
                    section
                    in self.completed_sections
                ),
                "facts": [
                    {
                        "field": fact.get(
                            "field"
                        ),
                        "value": fact.get(
                            "value"
                        ),
                        "negative": fact.get(
                            "negative",
                            False,
                        ),
                    }
                    for fact in self.section_facts(
                        section
                    )
                ],
            }

        return result

    def render_section(
        self,
        section: str,
    ) -> str | None:
        facts = self.section_facts(
            section
        )

        if not facts:
            return None

        lines: list[str] = []

        for fact in facts:
            field = str(
                fact.get("field")
                or "detail"
            ).replace(
                "_",
                " ",
            )

            value = fact.get(
                "value"
            )

            if isinstance(
                value,
                list,
            ):
                value_text = ", ".join(
                    str(item)
                    for item in value
                )
            else:
                value_text = str(
                    value
                )

            if fact.get(
                "negative"
            ):
                value_text = (
                    "No / not reported"
                )

            lines.append(
                f"{field}: {value_text}"
            )

        return "; ".join(
            dict.fromkeys(
                lines
            )
        )

    def custom_facts(
        self,
        section: str | None = None,
    ) -> list[dict[str, Any]]:
        facts = (
            self.facts
            if section is None
            else self.section_facts(
                section
            )
        )

        return [
            fact
            for fact in facts
            if str(
                fact.get("field")
                or ""
            ).startswith(
                "custom_"
            )
        ]

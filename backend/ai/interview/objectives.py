from __future__ import annotations


CORE_OBJECTIVES = (
    "chief_complaint",
    "onset",
)


TOPIC_PROFILES: dict[str, tuple[str, ...]] = {
    "headache": (
        "site",
        "severity",
        "character",
        "timing",
        "aggravating_factors",
        "relieving_factors",
        "vision_or_neuro",
        "nausea_vomiting",
    ),
    "chest_pain": (
        "site",
        "severity",
        "character",
        "timing",
        "aggravating_factors",
        "relieving_factors",
        "radiation",
        "breathing_difficulty",
        "associated_symptoms",
    ),
    "respiratory": (
        "onset",
        "severity",
        "timing",
        "breathing_difficulty",
        "cough",
        "wheeze",
        "associated_symptoms",
    ),
    "gastrointestinal": (
        "location",
        "severity",
        "timing",
        "nausea_vomiting",
        "bowel_changes",
        "associated_symptoms",
    ),
    "skin": (
        "site",
        "appearance",
        "itch_or_pain",
        "spread",
        "onset",
    ),
    "urinary": (
        "site",
        "severity",
        "urinary_frequency",
        "urinary_burning",
        "urinary_blood",
        "onset",
    ),
    "general": (
        "severity",
        "timing",
        "associated_symptoms",
    ),
}


TOPIC_ALIASES = {
    "migraine": "headache",
    "head pain": "headache",
    "cephalgia": "headache",
    "chest discomfort": "chest_pain",
    "breathlessness": "respiratory",
    "shortness of breath": "respiratory",
    "cough": "respiratory",
    "vomiting": "gastrointestinal",
    "stomach pain": "gastrointestinal",
    "abdominal pain": "gastrointestinal",
    "diarrhea": "gastrointestinal",
    "rash": "skin",
    "skin problem": "skin",
    "urine problem": "urinary",
    "urinary problem": "urinary",
}


def normalize_topic(topic: str | None) -> str:
    if not topic:
        return "general"

    value = topic.strip().lower().replace("-", "_")

    if value in TOPIC_PROFILES:
        return value

    return TOPIC_ALIASES.get(value, "general")


def objectives_for_topic(topic: str | None) -> tuple[str, ...]:
    normalized = normalize_topic(topic)

    return CORE_OBJECTIVES + TOPIC_PROFILES[normalized]


def missing_objectives(
    topic: str | None,
    known_fields: dict[str, object],
) -> list[str]:
    missing: list[str] = []

    for field in objectives_for_topic(topic):
        value = known_fields.get(field)

        # False is meaningful. We must never treat explicit negatives
        # as missing information.
        if value is None:
            missing.append(field)
        elif isinstance(value, str) and not value.strip():
            missing.append(field)

    # Avoid asking onset twice when a topic profile already includes it.
    result: list[str] = []

    for field in missing:
        if field not in result:
            result.append(field)

    return result

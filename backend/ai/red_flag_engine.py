from __future__ import annotations

import re
from typing import Any


def _normalise(text: str) -> str:
    text = text.lower()
    # Preserve Devanagari so Hindi and mixed-language safety signals reach
    # the rule engine instead of being stripped out.
    text = re.sub(r"[^a-z0-9\u0900-\u097f\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _contains(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def _contains_negated(text: str, phrase: str) -> bool:
    escaped = re.escape(phrase)

    patterns = (
        rf"\b(?:no|not|without|denies)\b[^.?!]{{0,30}}\b{escaped}\b",
        rf"\b{escaped}\b[^.?!]{{0,30}}\b(?:no|not|without|denies)\b",
        rf"(?:नहीं|नही|बिना)\s*.{{0,30}}{escaped}",
        rf"{escaped}.{{0,30}}(?:नहीं|नही)\b",
    )

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def detect_red_flags(
    clinical_text: str,
    structured_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Rule-based safety screen.

    This does not diagnose the patient.
    It identifies documented symptom combinations that should stop the
    interview and trigger physician/triage review.
    """

    structured_fields = structured_fields or {}

    text = _normalise(clinical_text)

    flags: list[str] = []
    critical_signals: dict[str, bool] = {}

    def add_flag(message: str, signal: str) -> None:
        if message not in flags:
            flags.append(message)
        critical_signals[signal] = True

    # ------------------------------------------------------------------
    # Chest pain
    # ------------------------------------------------------------------

    chest_pain_phrases = (
        "chest pain",
        "pain in my chest",
        "chest discomfort",
        "chest pressure",
        "pressure in my chest",
        "tightness in my chest",
        "सीने में दर्द",
        "सीने में दबाव",
        "सीने में जकड़न",
        "छाती में दर्द",
        "छाती में दबाव",
        "seene mein dard",
        "seene mein dabav",
        "seene mein jakdan",
        "seene mein bhari pan",
    )

    chest_pain = _contains(
        text,
        chest_pain_phrases,
    ) and not any(
        _contains_negated(
            text,
            phrase,
        )
        for phrase in chest_pain_phrases
    )

    character = _normalise(str(structured_fields.get("character", "")))
    radiation = _normalise(str(structured_fields.get("radiation", "")))
    associated = _normalise(
        str(structured_fields.get("associated_symptoms", ""))
    )
    aggravating = _normalise(
        str(structured_fields.get("aggravating_factors", ""))
    )
    relieving = _normalise(
        str(structured_fields.get("relieving_factors", ""))
    )

    chest_pressure = _contains(
        character,
        (
            "pressure",
            "squeezing",
            "crushing",
            "tight",
            "tightness",
            "heavy",
            "दबाव",
            "जकड़न",
            "भारी",
            "कसाव",
        ),
    )

    chest_radiation = _contains(
        radiation,
        (
            "arm",
            "shoulder",
            "jaw",
            "neck",
            "back",
            "हाथ",
            "कंधे",
            "जबड़े",
            "गर्दन",
            "पीठ",
        ),
    )

    sweating = _contains(
        f"{associated} {text}",
        (
            "sweating",
            "sweaty",
            "cold sweat",
            "पसीना",
            "पसीना आना",
        ),
    )

    exertional = _contains(
        aggravating,
        (
            "exercise",
            "exertion",
            "walking",
            "running",
            "stairs",
            "physical activity",
            "व्यायाम",
            "चलने",
            "दौड़ने",
            "सीढ़ी",
            "मेहनत",
        ),
    )

    rest_relief = _contains(
        relieving,
        (
            "rest",
            "sitting",
            "sitting down",
            "आराम",
            "बैठने",
            "बैठने से",
        ),
    )

    try:
        severity = float(structured_fields.get("severity", 0))
    except (TypeError, ValueError):
        severity = 0

    concerning_features = sum(
        (
            chest_pressure,
            chest_radiation,
            sweating,
            exertional,
            rest_relief,
            severity >= 7,
        )
    )

    if chest_pain and concerning_features >= 2:
        add_flag(
            "Chest pain with multiple concerning features requires prompt triage assessment.",
            "severe_chest_pain",
        )

    # ------------------------------------------------------------------
    # Severe breathing difficulty
    # ------------------------------------------------------------------

    breathing_phrases = (
        "difficulty breathing",
        "shortness of breath",
        "cannot breathe",
        "can't breathe",
        "struggling to breathe",
        "gasping",
        "सांस लेने में दिक्कत",
        "साँस लेने में दिक्कत",
        "सांस फूलना",
        "साँस फूलना",
        "दम घुटना",
        "साँस नहीं आ रही",
        "सांस नहीं आ रही",
        "saans phoolna",
        "saans lene mein dikkat",
        "saans nahi aa rahi",
        "saans nahin aa rahi",
        "dam ghutna",
        "saans lene mein mushkil",
    )

    breathing = _contains(
        text,
        breathing_phrases,
    )

    if breathing and not any(
        _contains_negated(
            text,
            phrase,
        )
        for phrase in breathing_phrases
    ):
        add_flag(
            "Severe breathing difficulty requires prompt triage assessment.",
            "severe_breathing_difficulty",
        )

    # ------------------------------------------------------------------
    # Loss of consciousness
    # ------------------------------------------------------------------

    if _contains(
        text,
        (
            "passed out",
            "fainted",
            "lost consciousness",
            "loss of consciousness",
            "unconscious",
            "passed unconscious",
            "बेहोश",
            "बेहोशी",
            "होश खो दिया",
            "behosh",
            "behoshi",
            "hosh kho diya",
        ),
    ):
        add_flag(
            "Loss of consciousness requires prompt physician assessment.",
            "loss_of_consciousness",
        )

    # ------------------------------------------------------------------
    # Stroke-like symptoms
    # ------------------------------------------------------------------

    stroke = _contains(
        text,
        (
            "face drooping",
            "facial droop",
            "sudden weakness",
            "one sided weakness",
            "one-sided weakness",
            "weakness on one side",
            "sudden numbness",
            "one sided numbness",
            "one-sided numbness",
            "difficulty speaking",
            "slurred speech",
            "speech difficulty",
            "चेहरा टेढ़ा",
            "अचानक कमजोरी",
            "एक तरफ कमजोरी",
            "एक तरफ सुन्नपन",
            "अचानक सुन्नपन",
            "बोलने में दिक्कत",
            "बोलने में परेशानी",
            "लड़खड़ाती बोली",
            "chehra tedha",
            "achanak kamzori",
            "ek taraf kamzori",
            "ek taraf sunnpan",
            "bolne mein dikkat",
            "bolne mein pareshani",
        ),
    )

    if stroke:
        add_flag(
            "Possible stroke-like symptoms require prompt triage assessment.",
            "stroke_symptoms",
        )

    # ------------------------------------------------------------------
    # Severe bleeding
    # ------------------------------------------------------------------

    bleeding = _contains(
        text,
        (
            "severe bleeding",
            "heavy bleeding",
            "bleeding heavily",
            "vomiting blood",
            "coughing blood",
            "बहुत ज्यादा खून",
            "तेज खून बहना",
            "खून की उल्टी",
            "खून की खांसी",
            "खून की खाँसी",
            "bahut zyada khoon",
            "tez khoon behna",
            "khoon ki ulti",
            "khoon ki khansi",
        ),
    )

    if bleeding:
        add_flag(
            "Severe bleeding requires prompt triage assessment.",
            "active_severe_bleeding",
        )

    # ------------------------------------------------------------------
    # Severe allergic reaction
    # ------------------------------------------------------------------

    airway_swelling = _contains(
        text,
        (
            "swollen tongue",
            "swelling of my tongue",
            "swollen throat",
            "swelling of my throat",
            "throat closing",
            "जीभ में सूजन",
            "गले में सूजन",
            "गला बंद",
            "jeebh mein sujan",
            "gale mein sujan",
            "gala band",
        ),
    )

    if airway_swelling and breathing:
        add_flag(
            "Possible severe allergic reaction requires prompt triage assessment.",
            "severe_allergic_reaction",
        )

    # ------------------------------------------------------------------
    # Severe/sudden headache
    # ------------------------------------------------------------------

    severe_headache = _contains(
        text,
        (
            "worst headache of my life",
            "thunderclap headache",
            "sudden severe headache",
            "very severe headache",
            "जिंदगी का सबसे तेज सिरदर्द",
            "अचानक बहुत तेज सिरदर्द",
            "बहुत तेज सिरदर्द",
            "अचानक तेज सिरदर्द",
            "zindagi ka sabse tez sir dard",
            "achanak bahut tez sir dard",
            "bahut tez sir dard",
            "achanak tez sir dard",
            "sabse tez sir dard",
        ),
    )

    if severe_headache:
        add_flag(
            "Severe or sudden headache requires prompt physician assessment.",
            "severe_headache",
        )

    return {
        "triage_required": bool(flags),
        "red_flags": flags,
        "critical_signals": critical_signals,
    }


# Backward-compatible names.
evaluate_red_flags = detect_red_flags
check_red_flags = detect_red_flags
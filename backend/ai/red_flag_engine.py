from __future__ import annotations

import re
from typing import Any


def _normalise(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _contains(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def _contains_negated(text: str, phrase: str) -> bool:
    patterns = (
        rf"\bno\b[^.?!]{{0,30}}\b{re.escape(phrase)}\b",
        rf"\bnot\b[^.?!]{{0,30}}\b{re.escape(phrase)}\b",
        rf"\bwithout\b[^.?!]{{0,30}}\b{re.escape(phrase)}\b",
        rf"\bdenies\b[^.?!]{{0,30}}\b{re.escape(phrase)}\b",
    )
    return any(re.search(pattern, text) for pattern in patterns)


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

    chest_pain = _contains(
        text,
        (
            "chest pain",
            "pain in my chest",
            "chest discomfort",
            "chest pressure",
            "pressure in my chest",
            "tightness in my chest",
        ),
    ) and not _contains_negated(text, "chest pain")

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
        ),
    )

    sweating = _contains(
        f"{associated} {text}",
        (
            "sweating",
            "sweaty",
            "cold sweat",
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
        ),
    )

    rest_relief = _contains(
        relieving,
        (
            "rest",
            "sitting",
            "sitting down",
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

    breathing = _contains(
        text,
        (
            "difficulty breathing",
            "shortness of breath",
            "cannot breathe",
            "can't breathe",
            "struggling to breathe",
            "gasping",
        ),
    )

    if breathing and not _contains_negated(text, "shortness of breath"):
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

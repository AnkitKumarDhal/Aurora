from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List


def _flatten_values(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for child in value.values():
            yield from _flatten_values(child)
        return

    if isinstance(value, list):
        for child in value:
            yield from _flatten_values(child)
        return

    if value is None:
        return

    yield str(value)


def _normalise(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _field_text(history: Dict[str, Any], section: str, field: str) -> str:
    section_data = history.get(section, {})
    if not isinstance(section_data, dict):
        return ""
    value = section_data.get(field, "")
    return _normalise(str(value)) if value is not None else ""


def _all_clinical_text(
    history: Dict[str, Any],
    raw_responses: List[Dict[str, Any]] | None,
) -> str:
    parts = list(_flatten_values(history))

    for item in raw_responses or []:
        if isinstance(item, dict):
            response = item.get("response") or item.get("patient_response")
            if response:
                parts.append(str(response))

    return _normalise(" ".join(parts))


def _patient_says_no(text: str) -> bool:
    return text in {
        "no",
        "nope",
        "nah",
        "none",
        "nothing",
        "none reported",
        "not really",
    }


def _add_unique(flags: List[str], flag: str) -> None:
    if flag not in flags:
        flags.append(flag)


def detect_red_flags(
    patient_history: Dict[str, Any] | str,
    raw_responses: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Rule-based safety screen.

    This is NOT a diagnosis engine. It identifies combinations of patient-
    reported features that warrant prompt physician/triage review.

    The important improvement here is combination logic: concerning
    chest-pain features can trigger triage even when no single sentence
    contains all keywords.
    """
    # Backward compatibility: older callers/tests passed a single patient
    # statement string instead of the structured clinical-history dictionary.
    # Treat that string as raw clinical text without changing the structured
    # dictionary interface used by ClinicalSession.
    legacy_text_input = isinstance(patient_history, str)

    if legacy_text_input:
        patient_text = patient_history
        patient_history = {
            "chief_complaint": patient_text,
            "history_of_present_illness": {},
        }
        raw_responses = list(raw_responses or [])
        raw_responses.append({"response": patient_text})
    elif not isinstance(patient_history, dict):
        patient_history = {}

    flags: List[str] = []

    text = _all_clinical_text(patient_history, raw_responses)

    hpi = patient_history.get("history_of_present_illness", {})
    if not isinstance(hpi, dict):
        hpi = {}

    character = _normalise(str(hpi.get("character", "")))
    radiation = _normalise(str(hpi.get("radiation", "")))
    associated = _normalise(str(hpi.get("associated_symptoms", "")))
    aggravating = _normalise(str(hpi.get("aggravating_factors", "")))
    relieving = _normalise(str(hpi.get("relieving_factors", "")))
    severity_raw = hpi.get("severity", "")
    site = _normalise(str(hpi.get("site", "")))

    # Older string-only callers did not have separate HPI fields. In that
    # compatibility mode, use the complete patient statement as the source
    # for each feature-specific screen. The structured ClinicalSession path
    # continues to use the individual HPI fields above.
    if legacy_text_input:
        character = text
        radiation = text
        associated = text
        aggravating = text
        relieving = text
        site = text

    chief_complaint = _normalise(
        str(patient_history.get("chief_complaint", ""))
    )

    # --------------------------------------------------------------
    # 1. Chest-pain combination screening
    # --------------------------------------------------------------

    chest_pain_text = f"{chief_complaint} {site} {text}"
    chest_pain_present = _contains_any(
        chest_pain_text,
        [
            "chest pain",
            "pain in my chest",
            "pain in chest",
            "chest discomfort",
            "pressure in my chest",
            "pressure on my chest",
            "tightness in my chest",
        ],
    )

    severe_pressure_character = _contains_any(
        character,
        [
            "squeezing",
            "crushing",
            "heavy pressure",
            "pressure",
            "tightness",
            "tight",
        ],
    )

    arm_or_shoulder_radiation = _contains_any(
        radiation,
        [
            "left arm",
            "right arm",
            "both arms",
            "arm",
            "left shoulder",
            "right shoulder",
            "shoulder",
            "jaw",
            "neck",
            "back",
        ],
    )

    sweating_present = _contains_any(
        associated,
        [
            "sweat",
            "sweaty",
            "sweating",
            "cold sweat",
            "profuse sweating",
        ],
    )

    exertional_worsening = _contains_any(
        aggravating,
        [
            "climb stairs",
            "stairs",
            "walking",
            "walk quickly",
            "running",
            "exercise",
            "exertion",
            "physical activity",
            "after exertion",
        ],
    )

    rest_relief = _contains_any(
        f"{relieving} {text}",
        [
            "rest makes it better",
            "rest helps",
            "better with rest",
            "relieved by rest",
            "sitting down and resting",
            "sitting and resting",
        ],
    )

    severe_numeric = False
    try:
        severe_numeric = float(severity_raw) >= 7
    except (TypeError, ValueError):
        pass

    # Consolidate overlapping chest-pain rules into one physician-facing alert.
    # Keep the legacy severe-chest-pain alert for that standalone test case.
    concerning_features = []

    if severe_pressure_character:
        concerning_features.append("pressure/squeezing character")
    if arm_or_shoulder_radiation:
        concerning_features.append("radiation")
    if sweating_present:
        concerning_features.append("sweating")
    if exertional_worsening:
        concerning_features.append("exertional worsening")
    if rest_relief:
        concerning_features.append("relief with rest")
    if severe_numeric:
        concerning_features.append("severity >= 7/10")

    concerning_chest_features = len(concerning_features)
    classic_high_concern = (
        arm_or_shoulder_radiation
        and (sweating_present or exertional_worsening or rest_relief)
    )

    if chest_pain_present and concerning_chest_features >= 2 or (
        chest_pain_present and classic_high_concern
    ):
        detail = ", ".join(concerning_features)
        message = (
            "Chest pain with multiple concerning features requires prompt "
            "triage assessment"
        )
        if detail:
            message += f": {detail}."
        else:
            message += "."
        _add_unique(flags, message)
    elif chest_pain_present and _contains_any(
        character,
        [
            "crushing",
            "severe pressure",
            "heavy squeezing",
            "squeezing pressure",
        ],
    ):
        _add_unique(
            flags,
            "Chest pain with pressure/squeezing character requires prompt physician assessment.",
        )
    elif chest_pain_present and "severe chest pain" in chest_pain_text:
        _add_unique(
            flags,
            "Severe chest pain requires prompt physician assessment.",
        )

    # --------------------------------------------------------------
    # 2. Breathing difficulty
    # --------------------------------------------------------------

    respiratory = _normalise(
        str(patient_history.get("respiratory_history", ""))
    )

    breathing_emergency = _contains_any(
        f"{respiratory} {text}",
        [
            "difficulty breathing",
            "shortness of breath",
            "severe shortness of breath",
            "severe difficulty breathing",
            "cannot breathe",
            "can't breathe",
            "struggling to breathe",
            "gasping",
        ],
    )

    if breathing_emergency:
        _add_unique(
            flags,
            "Severe breathing difficulty requires prompt triage assessment.",
        )

    # --------------------------------------------------------------
    # 3. Loss of consciousness
    # --------------------------------------------------------------

    if _contains_any(
        text,
        [
            "passed out",
            "fainted",
            "loss of consciousness",
            "lost consciousness",
            "unconscious",
        ],
    ):
        _add_unique(
            flags,
            "Loss of consciousness requires prompt physician assessment.",
        )

    # --------------------------------------------------------------
    # 4. Stroke-like symptoms
    # --------------------------------------------------------------

    stroke_pattern = (
        _contains_any(text, ["face drooping", "facial droop"])
        or _contains_any(
            text,
            [
                "sudden weakness",
                "sudden numbness",
                "one sided weakness",
                "one-sided weakness",
                "weakness on one side",
                "suddenly have weakness on one side",
                "one sided numbness",
                "one-sided numbness",
                "numbness on one side",
            ],
        )
        or _contains_any(
            text,
            [
                "difficulty speaking",
                "slurred speech",
                "speech difficulty",
            ],
        )
    )

    if stroke_pattern:
        _add_unique(
            flags,
            "Possible stroke-like symptoms require prompt triage assessment.",
        )

    # --------------------------------------------------------------
    # 5. Severe bleeding
    # --------------------------------------------------------------

    if _contains_any(
        text,
        [
            "severe bleeding",
            "heavy bleeding",
            "bleeding heavily",
            "vomiting blood",
            "coughing blood",
            "blood everywhere",
        ],
    ):
        _add_unique(
            flags,
            "Severe bleeding requires prompt triage assessment.",
        )

    # --------------------------------------------------------------
    # 6. Severe allergic reaction
    # --------------------------------------------------------------

    allergic_emergency = (
        _contains_any(
            text,
            [
                "swelling of my tongue",
                "swollen tongue",
                "swelling of my throat",
                "swollen throat",
                "throat closing",
                "cannot swallow",
            ],
        )
        and _contains_any(
            text,
            [
                "difficulty breathing",
                "shortness of breath",
                "struggling to breathe",
            ],
        )
    )

    if allergic_emergency:
        _add_unique(
            flags,
            "Possible severe allergic reaction requires prompt triage assessment.",
        )

    # --------------------------------------------------------------
    # 7. Severe headache with emergency-associated features
    # --------------------------------------------------------------

    severe_headache = _contains_any(
        text,
        [
            "worst headache of my life",
            "sudden severe headache",
            "thunderclap headache",
            "very severe headache",
        ],
    )

    if severe_headache:
        _add_unique(
            flags,
            "Severe or sudden headache requires prompt physician assessment.",
        )

    # --------------------------------------------------------------
    # Final decision
    # --------------------------------------------------------------

    # Older string-based callers/tests expect the original list-style result.
    # The structured ClinicalSession API continues to receive the dictionary
    # contract used throughout the current application.
    if legacy_text_input:
        return flags

    return {
        "triage_required": bool(flags),
        "red_flags": flags,
    }


# Backward-compatible aliases for callers that used an older name.
evaluate_red_flags = detect_red_flags
check_red_flags = detect_red_flags

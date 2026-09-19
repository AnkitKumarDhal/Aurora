from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, Optional, Tuple

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

OLLAMA_URL = os.getenv(
    "MEDIKIOSK_OLLAMA_URL",
    "http://127.0.0.1:11434/api/chat",
)

# Prefer the project-specific variables, but accept the older short names
# so local developers do not accidentally think AI has been disabled when
# testing with `AI_ENABLED=false`.
AI_ENABLED = (
    os.getenv(
        "MEDIKIOSK_AI_ENABLED",
        os.getenv("AI_ENABLED", "0"),
    )
    .strip()
    .lower()
    not in {"0", "false", "no", "off"}
)

AI_PROVIDER = os.getenv(
    "MEDIKIOSK_AI_PROVIDER",
    os.getenv("AI_PROVIDER", "auto"),
).strip().lower()

AI_TIMEOUT_SECONDS = float(
    os.getenv("MEDIKIOSK_AI_TIMEOUT", "15")
)

OLLAMA_MODEL = os.getenv(
    "MEDIKIOSK_OLLAMA_MODEL",
    "qwen2.5:3b",
)

OPENROUTER_PRIMARY_MODEL = os.getenv(
    "OPENROUTER_PRIMARY_MODEL",
    "google/gemma-4-31b-it:free",
)

OPENROUTER_FALLBACK_MODEL = os.getenv(
    "OPENROUTER_FALLBACK_MODEL",
    "openrouter/free",
)


_AI_COOLDOWN = False
_OLLAMA_STATUS_CACHE: Tuple[float, bool] = (0.0, False)


SIMPLE_NEGATIVE = {
    "no",
    "nope",
    "nah",
    "none",
    "nothing",
    "nothing else",
    "not really",
    "not applicable",
    "na",
    "n/a",
    "nil",
}

SIMPLE_POSITIVE = {
    "yes",
    "yeah",
    "yep",
    "y",
}


# ----------------------------------------------------------------------
# Supported semantic fields
# ----------------------------------------------------------------------

AI_SEMANTIC_FIELDS = {
    "onset",
    "site",
    "character",
    "radiation",
    "associated_symptoms",
    "timing",
    "aggravating_factors",
    "relieving_factors",
    "severity",
    "general_complaint",

    "medical_history",
    "surgical_history",
    "current_medications",
    "allergies",
    "family_history",
    "diet",
    "sleep",
    "smoking",
    "alcohol",
    "activity",

    "general",
    "respiratory",
    "cardiovascular",
    "gastrointestinal",
    "neurological",

    "respiratory_triggers",
    "cough",
    "sputum",
    "wheezing",
    "breathing_difficulty",

    # AYUSH / Dashavidha support
    "prakriti",
    "vikriti",
    "sara",
    "samhanana",
    "pramana",
    "satmya",
    "sattva",
    "ahara_shakti",
    "vyayama_shakti",
    "vaya",
    "ahara_vihara",
    "dashavidha",

    "gi_location",
    "nausea_vomiting",
    "bowel_changes",
    "appetite",
    "food_relation",

    "neuro_location",
    "dizziness",
    "weakness",
    "numbness",
    "vision",
    "headache_features",

    "skin_location",
    "appearance",
    "itching",
    "skin_pain",
    "changes",

    "urination_changes",
    "burning",
    "blood",
    "urgency",
    "urinary_associated_symptoms",
}


# ----------------------------------------------------------------------
# Field-specific instructions
# ----------------------------------------------------------------------

FIELD_INSTRUCTIONS = {
    "onset":
        "Extract when the symptom started or how long it has been present.",

    "site":
        "Extract the anatomical location of the symptom.",

    "character":
        "Extract how the patient describes the symptom quality, such as pressure, burning, throbbing, sharp, or dull.",

    "radiation":
        "Extract where the symptom spreads or radiates.",

    "associated_symptoms":
        "Extract other symptoms the patient explicitly reports alongside the main symptom.",

    "timing":
        "Extract the explicit timing pattern, such as continuous, intermittent, or episodes.",

    "aggravating_factors":
        "Extract what the patient explicitly says makes the symptom worse.",

    "relieving_factors":
        "Extract what the patient explicitly says makes the symptom better.",

    "severity":
        "Extract the explicit symptom severity, preferably as a number from 0 to 10 when stated.",

    "general_complaint":
        "Extract any additional complaint or concern explicitly mentioned.",

    "medical_history":
        "Extract previously diagnosed medical conditions explicitly mentioned.",

    "surgical_history":
        "Extract previous surgeries explicitly mentioned.",

    "current_medications":
        "Extract current medicines explicitly mentioned.",

    "allergies":
        "Extract allergies explicitly mentioned.",

    "family_history":
        "Extract important family medical conditions explicitly mentioned.",

    "diet":
        "Summarize the patient's stated usual diet without adding advice.",

    "sleep":
        "Summarize the patient's stated sleep pattern or quality.",

    "smoking":
        "Extract explicit smoking or tobacco-use information.",

    "alcohol":
        "Extract explicit alcohol-use information.",

    "activity":
        "Summarize the patient's stated physical activity.",

    "general":
        "Extract other general review-of-systems information explicitly stated.",

    "respiratory":
        "Extract other respiratory review-of-systems information explicitly stated.",

    "cardiovascular":
        "Extract other cardiovascular review-of-systems information explicitly stated.",

    "gastrointestinal":
        "Extract other gastrointestinal review-of-systems information explicitly stated.",

    "neurological":
        "Extract other neurological review-of-systems information explicitly stated.",

    "respiratory_triggers":
        "Extract explicit triggers of respiratory symptoms.",

    "cough":
        "Extract explicit cough information.",

    "sputum":
        "Extract explicit sputum/phlegm information.",

    "wheezing":
        "Extract explicit wheezing information.",

    "breathing_difficulty":
        "Extract explicit shortness of breath or breathing difficulty information.",

    "gi_location":
        "Extract the gastrointestinal anatomical location explicitly mentioned.",

    "nausea_vomiting":
        "Extract explicit nausea or vomiting information.",

    "bowel_changes":
        "Extract explicit diarrhea, constipation, or bowel-change information.",

    "appetite":
        "Extract explicit appetite information.",

    "food_relation":
        "Extract explicit statements linking symptoms to eating or food.",

    "neuro_location":
        "Extract the neurological symptom/discomfort location.",

    "dizziness":
        "Extract explicit dizziness or spinning information.",

    "weakness":
        "Extract explicit weakness or difficulty moving.",

    "numbness":
        "Extract explicit numbness or tingling.",

    "vision":
        "Extract explicit vision changes.",

    "headache_features":
        "Extract explicit headache quality/timing/features.",

    "skin_location":
        "Extract the skin symptom location.",

    "appearance":
        "Extract explicit skin appearance changes.",

    "itching":
        "Extract explicit itching information.",

    "skin_pain":
        "Extract explicit skin pain information.",

    "changes":
        "Extract explicit changes in the symptom over time.",

    "urination_changes":
        "Extract explicit changes in urination.",

    "burning":
        "Extract explicit burning with urination.",

    "blood":
        "Extract explicit blood in urine information.",

    "urgency":
        "Extract explicit urinary urgency.",

    # ------------------------------------------------------------------
    # AYUSH fields
    # ------------------------------------------------------------------

    "prakriti":
        "Extract the patient's stated Prakriti only; do not infer it.",

    "vikriti":
        "Extract the patient's stated Vikriti only; do not infer it.",

    "sara":
        "Extract provided Sara assessment only; do not infer it.",

    "samhanana":
        "Extract provided Samhanana assessment only; do not infer it.",

    "pramana":
        "Extract provided Pramana or body-measurement assessment only; do not infer it.",

    "satmya":
        "Extract provided Satmya or habituation assessment only; do not infer it.",

    "sattva":
        "Extract provided Sattva assessment only; do not infer it.",

    "ahara_shakti":
        "Extract provided Ahara Shakti assessment only; do not infer it.",

    "vyayama_shakti":
        "Extract provided Vyayama Shakti assessment only; do not infer it.",

    "vaya":
        "Extract provided Vaya assessment only; do not infer it.",

    "ahara_vihara":
        "Summarize only the patient's stated Ahara-Vihara (diet and lifestyle) information; do not add advice or infer a constitution.",

    "dashavidha":
        "Extract provided Dashavidha Pariksha information only; do not infer missing parameters.",
}


# ----------------------------------------------------------------------
# Small semantic guards
# ----------------------------------------------------------------------

_FIELD_QUALITY_HINTS = {
    "character": {
        "pressure",
        "squeezing",
        "tight",
        "tightness",
        "burning",
        "sharp",
        "dull",
        "throbbing",
        "aching",
        "stabbing",
        "cramping",
        "heavy",
        "tingling",
        "numb",
        "itching",
        "itchy",
        "stinging",
        "pulsing",
    },
}


_FIELD_ANATOMICAL_TOKENS = {
    "radiation": {
        "arm",
        "arms",
        "shoulder",
        "jaw",
        "neck",
        "back",
        "left arm",
        "right arm",
        "both arms",
        "leg",
        "legs",
    },
}


_FIELD_SYMPTOM_HINTS = {
    "associated_symptoms": {
        "sweating",
        "sweaty",
        "nausea",
        "vomiting",
        "dizziness",
        "breathlessness",
        "shortness of breath",
        "palpitations",
        "weakness",
        "numbness",
        "fever",
        "chills",
        "fainting",
        "cough",
        "wheezing",
        "fatigue",
        "headache",
        "diarrhea",
        "constipation",
    },
}


# Additional contextual safeguards.
#
# These are intentionally small and field-specific. They are NOT a giant
# keyword dictionary; they simply stop the adaptive extractor from assigning
# an answer to a field when the semantic role is clearly different.
_CONTEXTUAL_FIELD_HINTS = {
    "general_complaint": {
        "anything else",
        "anything more",
        "another problem",
        "another complaint",
        "other complaint",
        "other problem",
        "also have",
        "also having",
        "in addition",
        "apart from",
        "besides",
    },

    "aggravating_factors": {
        "worse",
        "worst",
        "increases",
        "gets worse",
        "trigger",
        "triggered",
        "aggravated",
    },

    "relieving_factors": {
        "better",
        "improves",
        "relieved",
        "helps",
        "rest",
        "after resting",
    },
}


def _validate_field_value(
    field: str,
    value: Any,
) -> bool:
    """
    Reject obvious cross-field semantic contamination from LLM output.

    This is NOT diagnostic logic. It simply prevents obviously wrong
    assignment between structured slots.
    """

    if value in (
        None,
        "",
        [],
        {},
    ):
        return False

    text = _normalised(
        value
    )

    if not text:
        return False

    if field == "character":
        return any(
            hint in text
            for hint in _FIELD_QUALITY_HINTS[
                "character"
            ]
        )

    if field == "radiation":
        return any(
            token in text
            for token in _FIELD_ANATOMICAL_TOKENS[
                "radiation"
            ]
        )

    if field == "associated_symptoms":
        return any(
            symptom in text
            for symptom in _FIELD_SYMPTOM_HINTS[
                "associated_symptoms"
            ]
        )

    return True


def _validate_contextual_field(
    field: str,
    value: Any,
    patient_response: str,
) -> bool:
    """
    Extra guard for adaptive multi-field extraction.

    The model is allowed to extract only when the patient's actual answer
    contains enough semantic evidence for that target field.
    """

    if not _validate_field_value(
        field,
        value,
    ):
        return False

    response_text = _normalised(
        patient_response
    )

    value_text = _normalised(
        value
    )

    if not response_text or not value_text:
        return False

    # general_complaint is especially vulnerable to false positives because
    # almost any sentence can look like an "additional complaint".
    if field == "general_complaint":
        return any(
            hint in response_text
            for hint in _CONTEXTUAL_FIELD_HINTS[
                "general_complaint"
            ]
        )

    # These fields have clear semantic triggers. If the answer does not
    # contain one, do not opportunistically fill them.
    if field in {
        "aggravating_factors",
        "relieving_factors",
    }:
        return any(
            hint in response_text
            for hint in _CONTEXTUAL_FIELD_HINTS[
                field
            ]
        )

    return True


# ----------------------------------------------------------------------
# Basic utilities
# ----------------------------------------------------------------------

def _clean(text: Any) -> str:
    return str(
        text or ""
    ).strip()


def _normalised(text: Any) -> str:
    return (
        _clean(text)
        .lower()
        .strip(
            " .!?\t\n"
        )
    )


def _json_from_text(
    text: str,
) -> Optional[Dict[str, Any]]:
    text = (
        text or ""
    ).strip()

    fenced = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        re.DOTALL | re.IGNORECASE,
    )

    if fenced:
        text = fenced.group(
            1
        ).strip()

    try:
        value = json.loads(
            text
        )

        return (
            value
            if isinstance(
                value,
                dict,
            )
            else None
        )

    except Exception:
        pass

    start = text.find(
        "{"
    )

    end = text.rfind(
        "}"
    )

    if start >= 0 and end > start:
        try:
            value = json.loads(
                text[
                    start:end + 1
                ]
            )

            return (
                value
                if isinstance(
                    value,
                    dict,
                )
                else None
            )

        except Exception:
            return None

    return None


def _number_from_text(
    text: str,
) -> Optional[int]:

    words = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }

    text = _normalised(
        text
    )

    for word, number in words.items():
        if re.search(
            rf"\b{re.escape(word)}\b",
            text,
        ):
            return number

    match = re.search(
        r"\b(10|[0-9])\b",
        text,
    )

    return (
        int(
            match.group(1)
        )
        if match
        else None
    )


# ----------------------------------------------------------------------
# Deterministic extraction
# ----------------------------------------------------------------------

def extract_explicit_onset(
    response: str,
) -> Optional[str]:

    text = _clean(
        response
    )

    lower = text.lower()

    patterns = [
        r"\bfor\s+(.+?)\s*$",
        r"\bsince\s+(.+?)\s*$",
        r"\bstarted\s+(.+?)\s*$",
        r"\bbegan\s+(.+?)\s*$",
        r"\bstarted\s+on\s+(.+?)\s*$",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            phrase = (
                match.group(1)
                .strip(
                    " .!?"
                )
            )

            if phrase:
                return phrase

    standalone = re.search(
        r"\b(today|yesterday|this morning|this evening|last night|a few days ago|\d+\s+(?:day|days|week|weeks|month|months|hour|hours) ago)\b",
        lower,
    )

    return (
        standalone.group(1)
        if standalone
        else None
    )


def _deterministic_extract(
    response: str,
    field: str,
) -> Dict[str, Any]:

    text = _clean(
        response
    )

    lower = _normalised(
        text
    )

    if not text:
        return {}

    if field == "severity":

        value = _number_from_text(
            text
        )

        return (
            {
                field: value
            }
            if value is not None
            else {}
        )

    if field == "timing":

        if any(
            x in lower
            for x in [
                "continuous",
                "constant",
                "always",
            ]
        ):
            return {
                field: "continuous"
            }

        if any(
            x in lower
            for x in [
                "comes and goes",
                "come and go",
                "intermittent",
                "on and off",
            ]
        ):
            return {
                field: "comes and goes"
            }

    if field == "onset":

        onset = extract_explicit_onset(
            text
        )

        return (
            {
                field: onset
            }
            if onset
            else {}
        )

    if field == "radiation":

        match = re.search(
            r"(?:spreads?|travels?|moves?|radiates?)\s+(?:to|toward|towards)\s+(.+)",
            text,
            re.I,
        )

        if match:
            return {
                field: (
                    match.group(1)
                    .strip(
                        " .!?"
                    )
                )
            }

    if field == "aggravating_factors":

        match = re.search(
            r"(?:worse|worst|increases?|gets worse)\s+(?:when|with|after)\s+(.+)",
            text,
            re.I,
        )

        if match:
            return {
                field: (
                    match.group(1)
                    .strip(
                        " .!?"
                    )
                )
            }

    if field == "relieving_factors":

        match = re.search(
            r"(?:better|improves?|relieved|helps?)\s+(?:when|with|after|by)?\s*(.+)",
            text,
            re.I,
        )

        if (
            match
            and any(
                key in lower
                for key in [
                    "better",
                    "improves",
                    "relieved",
                    "helps",
                ]
            )
        ):
            return {
                field: (
                    match.group(1)
                    .strip(
                        " .!?"
                    )
                )
            }

        # Specific handling for short phrases such as:
        # "rest helps"
        # "rest makes it better"
        # "better with rest"
        # "relieved by rest"
        if "rest" in lower and any(
            phrase in lower
            for phrase in [
                "better",
                "helps",
                "relieved",
                "improves",
            ]
        ):
            return {
                field: "rest"
            }

    if lower in SIMPLE_NEGATIVE:
        return {
            field: "None reported"
        }

    if lower in SIMPLE_POSITIVE:
        return {
            field: "Yes"
        }

    return {
        field: text
    }


# ----------------------------------------------------------------------
# Provider handling
# ----------------------------------------------------------------------

def _ollama_available() -> bool:
    global _OLLAMA_STATUS_CACHE

    now = time.time()

    cached_at, cached = (
        _OLLAMA_STATUS_CACHE
    )

    if now - cached_at < 20:
        return cached

    if requests is None:
        cached = False

    else:
        try:
            response = requests.get(
                OLLAMA_URL.replace(
                    "/api/chat",
                    "/api/tags",
                ),
                timeout=1.5,
            )

            cached = response.ok

        except Exception:
            cached = False

    _OLLAMA_STATUS_CACHE = (
        now,
        cached,
    )

    return cached


def _provider_order() -> list[str]:

    if (
        AI_PROVIDER
        in {
            "off",
            "disabled",
            "none",
        }
        or not AI_ENABLED
    ):
        return []

    if AI_PROVIDER == "ollama":
        return [
            "ollama"
        ]

    if AI_PROVIDER == "openrouter":
        return [
            "openrouter"
        ]

    order: list[str] = []

    if _ollama_available():
        order.append(
            "ollama"
        )

    if os.getenv(
        "OPENROUTER_API_KEY"
    ):
        order.append(
            "openrouter"
        )

    return order


def get_ai_status() -> Dict[str, Any]:
    return {
        "enabled": AI_ENABLED,
        "configured_provider": AI_PROVIDER,
        "ollama_available": _ollama_available(),
        "ollama_model": OLLAMA_MODEL,
        "openrouter_key_present": bool(
            os.getenv(
                "OPENROUTER_API_KEY"
            )
        ),
        "active_provider_order": _provider_order(),
    }


# ----------------------------------------------------------------------
# Prompt creation
# ----------------------------------------------------------------------

def _semantic_prompt(
    response: str,
    field: str,
) -> str:

    instruction = FIELD_INSTRUCTIONS.get(
        field,
        "Extract only information explicitly supported by the patient statement.",
    )

    return f"""You are the semantic extraction component of a clinical intake system.

Target field: {field}

Task:
{instruction}

Rules:
- Use ONLY facts explicitly stated or unambiguously expressed by the patient.
- Do NOT diagnose, suggest diseases, or invent missing information.
- Do NOT convert uncertainty into certainty.
- Extract the semantic role requested by the target field, not merely a phrase copied from the answer.
- Examples:
  - “right side of my chest” belongs to site
  - “left arm” belongs to radiation
  - “sweating” belongs to associated_symptoms
  - “climbing stairs” belongs to aggravating_factors
  - “rest” belongs to relieving_factors
- If the patient does not provide a usable value for this field, return null.
- Return JSON only:
  {{"value": <string or number or null>, "confidence": <number 0 to 1>}}

Patient response:
{response}
"""


# ----------------------------------------------------------------------
# Ollama
# ----------------------------------------------------------------------

def _call_ollama(
    prompt: str,
) -> Optional[Dict[str, Any]]:

    if requests is None:
        return None

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a conservative clinical-information "
                    "extraction assistant. Never diagnose."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "stream": False,
        "options": {
            "temperature": 0,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=AI_TIMEOUT_SECONDS,
        )

        if not response.ok:
            return None

        content = (
            response.json()
            .get(
                "message",
                {},
            )
            .get(
                "content",
                "",
            )
        )

        return _json_from_text(
            content
        )

    except Exception:
        return None


# ----------------------------------------------------------------------
# OpenRouter
# ----------------------------------------------------------------------

def _call_openrouter(
    prompt: str,
    model: str,
) -> Optional[Dict[str, Any]]:

    if requests is None:
        return None

    api_key = os.getenv(
        "OPENROUTER_API_KEY"
    )

    if not api_key:
        return None

    headers = {
        "Authorization":
            f"Bearer {api_key}",
        "Content-Type":
            "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a conservative clinical-information "
                    "extraction assistant. Never diagnose."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0,
        "response_format": {
            "type": "json_object",
        },
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=AI_TIMEOUT_SECONDS,
        )

        global _AI_COOLDOWN

        if response.status_code == 429:
            _AI_COOLDOWN = True
            return None

        if not response.ok:
            return None

        choices = (
            response.json()
            .get(
                "choices"
            )
            or []
        )

        if not choices:
            return None

        return _json_from_text(
            choices[0]
            .get(
                "message",
                {},
            )
            .get(
                "content",
                "",
            )
        )

    except Exception:
        return None


# ----------------------------------------------------------------------
# Single-field AI extraction
# ----------------------------------------------------------------------

def _try_ai_value(
    response: str,
    field: str,
) -> Optional[Dict[str, Any]]:

    prompt = _semantic_prompt(
        response,
        field,
    )

    for provider in _provider_order():

        parsed = (
            _call_ollama(
                prompt
            )
            if provider == "ollama"
            else None
        )

        if (
            provider == "openrouter"
            and not _AI_COOLDOWN
        ):

            parsed = _call_openrouter(
                prompt,
                OPENROUTER_PRIMARY_MODEL,
            )

            if (
                parsed is None
                and not _AI_COOLDOWN
            ):
                parsed = _call_openrouter(
                    prompt,
                    OPENROUTER_FALLBACK_MODEL,
                )

        if not isinstance(
            parsed,
            dict,
        ):
            continue

        value = parsed.get(
            "value"
        )

        if value in (
            None,
            "",
        ):
            continue

        try:
            confidence = float(
                parsed.get(
                    "confidence",
                    0.0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            confidence = 0.0

        if confidence < 0.50:
            continue

        if not _validate_field_value(
            field,
            value,
        ):
            continue

        return {
            field: value,
            "__extraction_method__":
                "ai",
            "__ai_provider__":
                provider,
            "__ai_confidence__":
                confidence,
        }

    return None


# ----------------------------------------------------------------------
# Adaptive contextual extraction
# ----------------------------------------------------------------------

def extract_contextual_fields(
    patient_response: str,
    candidate_fields: list[str],
) -> Dict[str, Any]:
    """
    Adaptive multi-field extraction from one patient statement.

    This is deliberately constrained to a caller-supplied allow-list of fields.

    The model may fill additional fields mentioned in the same answer, but it
    may not invent fields, change question order, diagnose, or infer missing
    data.
    """

    response = _clean(
        patient_response
    )

    candidates = []

    for field in (
        candidate_fields or []
    ):
        field = _clean(
            field
        )

        if (
            field
            and field in FIELD_INSTRUCTIONS
            and field not in candidates
        ):
            candidates.append(
                field
            )

    # Adaptive extraction is deliberately conservative.
    # Short answers should normally be handled by the current deterministic
    # field instead of being interpreted against every remaining field.
    if (
        not response
        or len(response.split()) < 6
        or not candidates
        or not _provider_order()
    ):
        return {}

    instructions = "\n".join(
        f"- {field}: {FIELD_INSTRUCTIONS[field]}"
        for field in candidates
    )

    prompt = f"""You are the adaptive semantic-extraction component of a clinical intake system.

Review the patient's single answer and extract any OTHER fields from the allowed list that are explicitly present in the same answer.

Rules:
- Use only information explicitly stated by the patient.
- Do not infer diagnoses, causes, severity, or missing facts.
- Do not create fields outside the allowed list.
- Do not fill a field just because it would be clinically plausible.
- A field may be omitted when the patient did not explicitly provide that information.
- Preserve the patient's meaning; do not rewrite into a medical diagnosis.
- Assign each phrase to the field that matches its semantic role.
- Never copy an anatomical location into character or associated_symptoms.
- Never copy radiation into associated_symptoms.
- Never copy a relieving factor into general_complaint.
- Never copy an aggravating factor into general_complaint.
- Example:
  “right side of chest” -> site
  “left arm” -> radiation
  “sweating” -> associated_symptoms
  “climbing stairs” -> aggravating_factors
  “rest” -> relieving_factors
- Return JSON only in this exact shape:
  {{"fields": {{"field_name": value, ...}}}}

ALLOWED FIELDS:
{instructions}

PATIENT ANSWER:
{response}
"""

    for provider in _provider_order():

        parsed = (
            _call_ollama(
                prompt
            )
            if provider == "ollama"
            else None
        )

        if (
            provider == "openrouter"
            and not _AI_COOLDOWN
        ):

            parsed = _call_openrouter(
                prompt,
                OPENROUTER_PRIMARY_MODEL,
            )

            if (
                parsed is None
                and not _AI_COOLDOWN
            ):
                parsed = _call_openrouter(
                    prompt,
                    OPENROUTER_FALLBACK_MODEL,
                )

        if not isinstance(
            parsed,
            dict,
        ):
            continue

        fields = parsed.get(
            "fields"
        )

        if not isinstance(
            fields,
            dict,
        ):
            # Tolerate models that return the field mapping directly.
            fields = parsed

        clean_fields: Dict[str, Any] = {}

        for field in candidates:

            value = fields.get(
                field
            )

            if value in (
                None,
                "",
                [],
                {},
            ):
                continue

            if (
                isinstance(
                    value,
                    (
                        str,
                        int,
                        float,
                        bool,
                    ),
                )
                and _validate_contextual_field(
                    field,
                    value,
                    response,
                )
            ):
                clean_fields[field] = value

        if clean_fields:
            return {
                **clean_fields,
                "__extraction_method__":
                    "ai_contextual",
                "__ai_provider__":
                    provider,
                "__ai_fields__":
                    list(
                        clean_fields.keys()
                    ),
            }

    return {}


# ----------------------------------------------------------------------
# Public extraction function
# ----------------------------------------------------------------------

def extract_history(
    patient_response: str,
    field: str,
) -> Dict[str, Any]:

    response = _clean(
        patient_response
    )

    field = _clean(
        field
    )

    deterministic = _deterministic_extract(
        response,
        field,
    )

    normalised = _normalised(
        response
    )

    if (
        field not in AI_SEMANTIC_FIELDS
        or normalised in SIMPLE_NEGATIVE
        or normalised in SIMPLE_POSITIVE
        or len(response.split()) < 3
    ):

        deterministic[
            "__extraction_method__"
        ] = "deterministic"

        return deterministic

    deterministic_value = (
        deterministic.get(
            field
        )
    )

    # If deterministic extraction already found a useful specific value,
    # don't spend an AI call rewriting it.
    deterministic_is_specific = (
        deterministic_value not in (
            None,
            "",
        )
        and self_value_differs_from_response(
            deterministic_value,
            response,
        )
    )

    if deterministic_is_specific:

        deterministic[
            "__extraction_method__"
        ] = "deterministic"

        return deterministic

    ai_result = _try_ai_value(
        response,
        field,
    )

    if ai_result:
        return ai_result

    deterministic[
        "__extraction_method__"
    ] = "deterministic"

    return deterministic


def self_value_differs_from_response(
    value: Any,
    response: str,
) -> bool:

    left = _normalised(
        value
    )

    right = _normalised(
        response
    )

    return left != right


# ----------------------------------------------------------------------
# AI physician summary
# ----------------------------------------------------------------------

def generate_ai_physician_summary(
    structured_case: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Generate an additive physician-facing narrative draft.

    Structured facts remain the source of truth.
    """

    if (
        not isinstance(
            structured_case,
            dict,
        )
        or not _provider_order()
    ):
        return None

    prompt = f"""Create a concise physician-facing narrative draft from the structured case below.

Rules:
- Use only facts present in the supplied data.
- Do not diagnose, prescribe, or infer causation.
- Mention uncertainty or contradictions when present.
- Highlight the existing triage/red-flag state without adding new clinical conclusions.
- Structured fields remain the source of truth; this is only a readable draft.
- Return JSON only:
  {{"summary": "...", "key_points": ["...", "..."]}}

STRUCTURED CASE:
{json.dumps(
    structured_case,
    ensure_ascii=False,
    indent=2,
)}
"""

    for provider in _provider_order():

        parsed = (
            _call_ollama(
                prompt
            )
            if provider == "ollama"
            else None
        )

        if (
            provider == "openrouter"
            and not _AI_COOLDOWN
        ):
            parsed = _call_openrouter(
                prompt,
                OPENROUTER_PRIMARY_MODEL,
            )

        if (
            isinstance(
                parsed,
                dict,
            )
            and parsed.get(
                "summary"
            )
        ):
            return {
                "provider":
                    provider,

                "model": (
                    OLLAMA_MODEL
                    if provider == "ollama"
                    else OPENROUTER_PRIMARY_MODEL
                ),

                "summary":
                    str(
                        parsed[
                            "summary"
                        ]
                    ),

                "key_points": [
                    str(x)
                    for x in (
                        parsed.get(
                            "key_points"
                        )
                        or []
                    )
                ],
            }

    return None


# ----------------------------------------------------------------------
# AI red-flag secondary screen
# ----------------------------------------------------------------------

def analyze_red_flags_with_ai(
    patient_text: str,
) -> Optional[Dict[str, Any]]:
    """
    Secondary AI safety screen.

    Deterministic rules remain authoritative.

    The model may identify a possible emergency pattern from the supplied
    patient text, but it never diagnoses.
    """

    text = _clean(
        patient_text
    )

    if (
        len(text.split()) < 4
        or not _provider_order()
    ):
        return None

    prompt = f"""You are a conservative clinical safety-screen assistant.

Review only the patient text below.

Identify explicit emergency warning signs that should receive prompt
physician/triage attention.

Do not diagnose.
Do not infer hidden symptoms.

Return JSON only:
{{"urgent": true|false, "flags": ["short factual warning", ...]}}

PATIENT TEXT:
{text}
"""

    for provider in _provider_order():

        parsed = (
            _call_ollama(
                prompt
            )
            if provider == "ollama"
            else None
        )

        if (
            provider == "openrouter"
            and not _AI_COOLDOWN
        ):
            parsed = _call_openrouter(
                prompt,
                OPENROUTER_PRIMARY_MODEL,
            )

        if not isinstance(
            parsed,
            dict,
        ):
            continue

        flags = (
            parsed.get(
                "flags"
            )
            or []
        )

        if isinstance(
            flags,
            str,
        ):
            flags = [
                flags
            ]

        clean_flags = [
            str(flag).strip()
            for flag in flags
            if str(flag).strip()
        ]

        urgent = (
            bool(
                parsed.get(
                    "urgent"
                )
            )
            and bool(
                clean_flags
            )
        )

        return {
            "provider":
                provider,
            "urgent":
                urgent,
            "flags":
                clean_flags,
        }

    return None
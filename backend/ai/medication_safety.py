from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Conservative, explicit interaction rules.
# ---------------------------------------------------------------------------
#
# This is intentionally NOT a complete drug-interaction database.
# It is a transparent safety screen for a small set of high-confidence pairs.
# A "no alert" result must never be interpreted as "no interactions exist".
#
# The rules below are based on FDA labeling / FDA interaction information,
# including warnings for:
#   - anticoagulant + NSAID bleeding risk
#   - methotrexate + trimethoprim/sulfamethoxazole or penicillins
#   - clarithromycin + simvastatin/lovastatin
#   - clarithromycin + colchicine
#
# The caller should keep the result physician-reviewable and source-aware.
# ---------------------------------------------------------------------------

RULES: List[Dict[str, Any]] = [
    {
        "rule_id": "warfarin-nsaid",
        "groups": [
            {"warfarin"},
            {
                "ibuprofen",
                "naproxen",
                "diclofenac",
                "indomethacin",
                "ketoprofen",
                "aspirin",
            },
        ],
        "severity": "high",
        "message": (
            "Anticoagulant with NSAID or antiplatelet therapy may increase bleeding risk."
        ),
        "action": (
            "Prompt physician/pharmacist review of the medication combination is required."
        ),
        "evidence_basis": "FDA labeling for NSAIDs/warfarin and hemostasis-interfering drugs.",
    },
    {
        "rule_id": "warfarin-tmp-sulfa",
        "groups": [
            {"warfarin"},
            {
                "trimethoprim sulfamethoxazole",
                "trimethoprim/sulfamethoxazole",
                "co trimoxazole",
                "cotrimoxazole",
                "tmp smx",
            },
        ],
        "severity": "high",
        "message": (
            "Warfarin with trimethoprim/sulfamethoxazole requires interaction review and monitoring."
        ),
        "action": "Physician/pharmacist review is required.",
        "evidence_basis": "Known anticoagulant interaction; not a dosing recommendation.",
    },
    {
        "rule_id": "methotrexate-tmp-sulfa",
        "groups": [
            {"methotrexate"},
            {
                "trimethoprim sulfamethoxazole",
                "trimethoprim/sulfamethoxazole",
                "co trimoxazole",
                "cotrimoxazole",
                "tmp smx",
            },
        ],
        "severity": "high",
        "message": (
            "Methotrexate with trimethoprim/sulfamethoxazole has a reported bone-marrow suppression risk."
        ),
        "action": "Prompt physician/pharmacist review is required.",
        "evidence_basis": "FDA methotrexate labeling.",
    },
    {
        "rule_id": "methotrexate-penicillin",
        "groups": [
            {"methotrexate"},
            {
                "penicillin",
                "amoxicillin",
                "ampicillin",
                "penicillin v",
            },
        ],
        "severity": "high",
        "message": (
            "Penicillins may reduce methotrexate renal clearance and can increase methotrexate exposure."
        ),
        "action": "Prompt physician/pharmacist review is required.",
        "evidence_basis": "FDA methotrexate labeling.",
    },
    {
        "rule_id": "clarithromycin-simvastatin",
        "groups": [
            {"clarithromycin"},
            {"simvastatin", "lovastatin"},
        ],
        "severity": "high",
        "message": (
            "Clarithromycin can substantially increase exposure to simvastatin/lovastatin."
        ),
        "action": "Prompt physician/pharmacist review is required.",
        "evidence_basis": "FDA clarithromycin/statin labeling.",
    },
    {
        "rule_id": "clarithromycin-colchicine",
        "groups": [
            {"clarithromycin"},
            {"colchicine"},
        ],
        "severity": "high",
        "message": (
            "Clarithromycin with colchicine has a clinically important toxicity interaction."
        ),
        "action": "Prompt physician/pharmacist review is required.",
        "evidence_basis": "FDA clarithromycin/colchicine labeling.",
    },
]


def _normalise_name(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9/+ -]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _canonical_names(name: str) -> List[str]:
    """Return normalized aliases for safe exact-set matching."""
    normalized = _normalise_name(name)
    aliases = {normalized}

    replacements = {
        "co-trimoxazole": "co trimoxazole",
        "co trimoxazole": "trimethoprim sulfamethoxazole",
        "trimethoprim/sulfamethoxazole": "trimethoprim sulfamethoxazole",
        "tmp/smx": "tmp smx",
        "penicillin v": "penicillin",
    }

    if normalized in replacements:
        aliases.add(replacements[normalized])

    return sorted(aliases)


def _rule_matches(names_a: str, names_b: str, rule: Dict[str, Any]) -> bool:
    groups = rule.get("groups", [])
    if len(groups) != 2:
        return False

    aliases_a = set(_canonical_names(names_a))
    aliases_b = set(_canonical_names(names_b))

    left = aliases_a.intersection(groups[0]) and aliases_b.intersection(groups[1])
    right = aliases_a.intersection(groups[1]) and aliases_b.intersection(groups[0])
    return bool(left or right)


def _flatten_medications(
    medications: Iterable[Any],
) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []

    for item in medications:
        if not isinstance(item, dict):
            continue

        name = item.get("name")
        if not name:
            continue

        result.append(
            {
                "name": str(name),
                "normalized_name": _normalise_name(name),
                "source": item.get("source") or "unknown",
                "source_text": item.get("source_text"),
            }
        )

    return result


def screen_medication_interactions(
    medications: Optional[Iterable[Any]] = None,
) -> Dict[str, Any]:
    """
    Screen a structured medication list against a small explicit rule set.

    Returns a physician-reviewable result. A clean result means that none of
    the supported built-in rules matched; it does NOT mean that all possible
    drug interactions have been excluded.
    """
    items = _flatten_medications(medications or [])
    alerts: List[Dict[str, Any]] = []

    for index, first in enumerate(items):
        for second in items[index + 1 :]:
            for rule in RULES:
                if not _rule_matches(
                    first["name"],
                    second["name"],
                    rule,
                ):
                    continue

                alert = {
                    "rule_id": rule["rule_id"],
                    "severity": rule["severity"],
                    "medications": [
                        first["name"],
                        second["name"],
                    ],
                    "message": rule["message"],
                    "action": rule["action"],
                    "evidence_basis": rule["evidence_basis"],
                    "requires_physician_review": True,
                }

                if alert not in alerts:
                    alerts.append(alert)

    return {
        "status": "alert" if alerts else "no_supported_rule_match",
        "screened_medications": [
            {
                "name": item["name"],
                "source": item["source"],
            }
            for item in items
        ],
        "potential_interactions": alerts,
        "interaction_count": len(alerts),
        "requires_physician_review": bool(alerts),
        "scope": "limited_builtin_rules",
        "disclaimer": (
            "No alert means only that no supported built-in rule matched. "
            "This is not a complete drug-interaction database and does not "
            "replace pharmacist/physician review."
        ),
    }


__all__ = [
    "RULES",
    "screen_medication_interactions",
]

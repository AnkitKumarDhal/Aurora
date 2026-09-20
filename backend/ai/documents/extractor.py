from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _first_match(text: str, patterns: List[str]) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            value = _clean(match.group(1))
            if value:
                return value
    return None


def _document_type_from_text(text: str) -> str:
    t = text.lower()

    prescription_terms = [
        "prescription",
        "rx:",
        "tablet",
        "capsule",
        "syrup",
        "dose",
        "dosage",
        "mg",
        "ml",
        "dispense/supply",
        "sig:",
    ]

    lab_terms = [
        "lab report",
        "laboratory",
        "reference range",
        "test result",
        "hemoglobin",
        "haemoglobin",
        "wbc",
        "rbc",
        "platelet",
        "glucose",
        "creatinine",
    ]

    discharge_terms = [
        "discharge summary",
        "discharged",
        "hospital course",
        "discharge diagnosis",
        "follow-up",
        "follow up",
    ]

    scores = {
        "prescription": sum(x in t for x in prescription_terms),
        "lab_report": sum(x in t for x in lab_terms),
        "discharge_summary": sum(x in t for x in discharge_terms),
    }

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"


def _extract_identity(text: str) -> Dict[str, Optional[str]]:
    patient_name = _first_match(
        text,
        [
            r"\bpatient\s+name\s*[:\-]?\s*(.*?)(?=\s*[^A-Za-z0-9]*(?:birthdate|date|dob|age|sex|mrn|allergies)\b|$)",
            r"\bname\s*[:\-]?\s*(.*?)(?=\s*[^A-Za-z0-9]*(?:birthdate|date|dob|age|sex|mrn|allergies)\b|$)",
        ],
    )

    date = _first_match(
        text,
        [
            r"\bdate\s+issued\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            r"\bdate\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            r"\bdate\s*[:\-]?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
        ],
    )

    return {
        "patient_name": patient_name.strip(" .:-'\"‘’")
        if patient_name
        else None,
        "date": date,
    }


def _split_prescription_items(text: str) -> List[str]:
    normalized = _clean(text)

    matches = list(
        re.finditer(
            r"\bRx\s*:\s*",
            normalized,
            flags=re.IGNORECASE,
        )
    )

    if not matches:
        return []

    items: List[str] = []

    stop_match = re.search(
        r"\b(?:DISPENSE\s+AS\s+WRITTEN|SUBSTITUTION\s+PERMITTED)\b",
        normalized,
        flags=re.IGNORECASE,
    )

    stop_position = stop_match.start() if stop_match else len(normalized)

    for index, match in enumerate(matches):
        start = match.end()

        next_rx = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else stop_position
        )

        end = min(next_rx, stop_position)

        if start >= end:
            continue

        item = normalized[start:end].strip(" .,:;-")

        if item:
            items.append(item)

    return items


def _extract_strength(item: str) -> tuple[Optional[str], Optional[re.Match[str]]]:
    patterns = [
        r"\b\d+(?:\s*[-/]\s*\d+)?\s*(?:mg|mcg|g|ml)(?:\s*/\s*\d+\s*(?:hours?|hrs?|hr|h))?\b",
        r"\b\d+(?:\s*[-/]\s*\d+)?\s*(?:mg|mcg|g|ml)\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            item,
            flags=re.IGNORECASE,
        )

        if match:
            return _clean(match.group(0)), match

    return None, None


def _extract_dose(item: str) -> Optional[str]:
    patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:tablets?|tabs?|capsules?|caps?|drops?|puffs?|ml)\b",
        r"=\s*[|Il1]\s*(?:tab|tabs|tablet|tablets|cap|capsule|capsules)\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            item,
            flags=re.IGNORECASE,
        )

        if match:
            value = _clean(match.group(0))

            if value.startswith("="):
                return "1 tab"

            return value

    return None


def _extract_frequency(item: str) -> Optional[str]:
    matches: List[str] = []

    qh_matches = list(
        re.finditer(
            r"\bQ\d+\s*H(?:\s+PRN)?\b",
            item,
            flags=re.IGNORECASE,
        )
    )

    for match in qh_matches:
        value = _clean(match.group(0))

        if value not in matches:
            matches.append(value.upper())

    daily_matches = list(
        re.finditer(
            r"\b(?:once|twice|three|four)\s+(?:a|per)\s+day\b",
            item,
            flags=re.IGNORECASE,
        )
    )

    for match in daily_matches:
        value = _clean(match.group(0)).lower()

        if value not in matches:
            matches.append(value)

    numeric_daily_matches = list(
        re.finditer(
            r"\b\d+\s+times\s+(?:a|per)\s+day\b",
            item,
            flags=re.IGNORECASE,
        )
    )

    for match in numeric_daily_matches:
        value = _clean(match.group(0)).lower()

        if value not in matches:
            matches.append(value)

    simple_matches = list(
        re.finditer(
            r"\b(?:once|twice|three|four)\s+daily\b",
            item,
            flags=re.IGNORECASE,
        )
    )

    for match in simple_matches:
        value = _clean(match.group(0)).lower()

        if value not in matches:
            matches.append(value)

    cadence_matches = list(
        re.finditer(
            r"\b(?:daily|weekly|monthly)\b",
            item,
            flags=re.IGNORECASE,
        )
    )

    for match in cadence_matches:
        value = _clean(match.group(0)).lower()

        if value not in matches:
            matches.append(value)

    prn_present = bool(
        re.search(
            r"\bPRN\b|\bas\s+needed\b",
            item,
            flags=re.IGNORECASE,
        )
    )

    if prn_present and not any(
        "PRN" in value.upper()
        for value in matches
    ):
        matches.append("PRN")

    acronym_matches = list(
        re.finditer(
            r"\b(?:OD|BD|TID|QID)\b",
            item,
            flags=re.IGNORECASE,
        )
    )

    for match in acronym_matches:
        value = _clean(match.group(0)).upper()

        if value not in matches:
            matches.append(value)

    return " ".join(matches) if matches else None


def _extract_timing(item: str) -> Optional[str]:
    patterns = [
        r"\b(?:before|after)\s+(?:food|meals?|breakfast|lunch|dinner)\b",
        r"\bat\s+bedtime\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            item,
            flags=re.IGNORECASE,
        )

        if match:
            return _clean(match.group(0))

    return None


def _extract_medication_item(item: str) -> Dict[str, Optional[str]]:
    item = _clean(item)

    strength, strength_match = _extract_strength(item)
    dose = _extract_dose(item)
    frequency = _extract_frequency(item)
    timing = _extract_timing(item)

    cut_positions: List[int] = []

    if strength_match:
        cut_positions.append(strength_match.start())

    for pattern in [
        r"\bstart\s+date\b",
        r"\bsig\s*:",
        r"\bdispense\s*/\s*supply\b",
        r"\brefill\b",
        r"\bq\d+\s*h\b",
        r"\bdaily\b",
        r"\bprn\b",
        r"\bbefore\s+(?:food|meals?|breakfast|lunch|dinner)\b",
        r"\bafter\s+(?:food|meals?|breakfast|lunch|dinner)\b",
    ]:
        match = re.search(
            pattern,
            item,
            flags=re.IGNORECASE,
        )

        if match:
            cut_positions.append(match.start())

    cut_at = min(cut_positions) if cut_positions else len(item)

    name = _clean(item[:cut_at]).strip(" ,-:")

    name = re.sub(
        r"\b(?:oral|tablet|tablets|capsule|capsules|tab|tabs|cap|caps)\b",
        " ",
        name,
        flags=re.IGNORECASE,
    )

    name = re.sub(r"\s+", " ", name).strip(" ,-:")

    return {
        "name": name or None,
        "strength": strength,
        "dose": dose,
        "frequency": frequency,
        "timing": timing,
        "source_text": item,
    }


def _extract_prescription(text: str) -> Dict[str, Any]:
    identity = _extract_identity(text)
    items = _split_prescription_items(text)

    medications = [
        medication
        for medication in (
            _extract_medication_item(item)
            for item in items
        )
        if medication.get("name")
    ]

    return {
        "document_type": "prescription",
        "patient_name": identity["patient_name"],
        "date": identity["date"],
        "medications": medications,
        "follow_up": _extract_follow_up(text),
    }


def _extract_follow_up(text: str) -> Optional[str]:
    match = re.search(
        r"\bfollow[- ]?up\b\s*(?:after|in|on)?\s*([^.;]+)",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    value = _clean(match.group(0))
    return value or None


def _extract_lab(text: str) -> Dict[str, Any]:
    identity = _extract_identity(text)
    tests: List[Dict[str, Optional[str]]] = []

    pattern = re.compile(
        r"([A-Za-z][A-Za-z0-9 /()._-]{1,50}?)\s+"
        r"([<>]?\s*\d+(?:\.\d+)?)\s*"
        r"([A-Za-z/%µμ^0-9.-]+)?$",
        flags=re.IGNORECASE,
    )

    ignored = {
        "patient",
        "date",
        "prescription",
        "reference range",
        "test result",
    }

    for raw_line in text.splitlines():
        line = _clean(raw_line)

        if not line:
            continue

        match = pattern.fullmatch(line)

        if not match:
            continue

        name = _clean(match.group(1))

        if name.lower() in ignored:
            continue

        tests.append(
            {
                "test": name,
                "value": _clean(match.group(2)),
                "unit": _clean(match.group(3) or "") or None,
            }
        )

    return {
        "document_type": "lab_report",
        "patient_name": identity["patient_name"],
        "date": identity["date"],
        "tests": tests,
    }


def _extract_discharge(text: str) -> Dict[str, Any]:
    identity = _extract_identity(text)

    diagnosis = _first_match(
        text,
        [
            r"\bdischarge\s+diagnosis\s*[:\-]\s*([^\n]+)",
            r"\bdiagnosis\s*[:\-]\s*([^\n]+)",
        ],
    )

    hospital_course = _first_match(
        text,
        [
            r"\bhospital\s+course\s*[:\-]\s*([^\n]+)",
        ],
    )

    follow_up = _extract_follow_up(text)

    return {
        "document_type": "discharge_summary",
        "patient_name": identity["patient_name"],
        "date": identity["date"],
        "diagnosis": diagnosis,
        "hospital_course": hospital_course,
        "follow_up": follow_up,
    }


def extract_document(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(ocr_result, dict):
        raise TypeError("ocr_result must be a dictionary")

    raw_text = str(ocr_result.get("text") or "")

    document_type = str(
        ocr_result.get("document_type")
        or _document_type_from_text(raw_text)
    ).strip().lower()

    if document_type == "prescription":
        structured = _extract_prescription(raw_text)
    elif document_type == "lab_report":
        structured = _extract_lab(raw_text)
    elif document_type == "discharge_summary":
        structured = _extract_discharge(raw_text)
    else:
        identity = _extract_identity(raw_text)

        structured = {
            "document_type": "unknown",
            "patient_name": identity["patient_name"],
            "date": identity["date"],
        }

    review_reasons = list(
        ocr_result.get("review_reasons") or []
    )

    manual_review = bool(
        ocr_result.get("manual_review_required", False)
    )

    if document_type == "prescription" and not structured.get("medications"):
        manual_review = True
        review_reasons.append(
            "No prescription medication entries could be confidently extracted."
        )

    if document_type == "lab_report" and not structured.get("tests"):
        manual_review = True
        review_reasons.append(
            "No laboratory test/value pairs could be confidently extracted."
        )

    if document_type == "unknown":
        manual_review = True
        review_reasons.append(
            "Document type could not be confidently determined."
        )

    if not structured.get("patient_name"):
        manual_review = True
        review_reasons.append(
            "Patient name could not be confidently extracted from OCR."
        )

    return {
        "status": "success",
        "document_type": structured.get(
            "document_type",
            document_type,
        ),
        "patient_name": structured.get(
            "patient_name",
        ),
        "date": structured.get(
            "date",
        ),
        "structured_data": structured,
        "raw_text": raw_text,
        "ocr_confidence": ocr_result.get(
            "mean_confidence",
        ),
        "manual_review_required": manual_review,
        "review_reasons": list(
            dict.fromkeys(review_reasons)
        ),
    }

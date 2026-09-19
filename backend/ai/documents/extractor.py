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
        "rx",
        "tablet",
        "capsule",
        "syrup",
        "dose",
        "dosage",
        "mg",
        "ml",
        "before food",
        "after food",
        "before breakfast",
        "after breakfast",
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
    # OCR often flattens the whole page into one line, so do not depend
    # on newline boundaries here.
    patient_name = _first_match(
        text,
        [
            r"\bpatient\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]{1,60}?)(?=\s+\bdate\b|\s+\bdob\b|\s+\bage\b|$)",
            r"\bname\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]{1,60}?)(?=\s+\bdate\b|\s+\bdob\b|\s+\bage\b|$)",
        ],
    )

    date = _first_match(
        text,
        [
            r"\bdate\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            r"\bdate\s*[:\-]?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
        ],
    )

    return {
        "patient_name": patient_name,
        "date": date,
    }


def _split_prescription_items(text: str) -> List[str]:
    normalized = _clean(text)

    matches = list(
        re.finditer(r"(?:^|\s)(\d+)\.\s*", normalized)
    )

    if not matches:
        return []

    items: List[str] = []

    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(normalized)
        item = normalized[start:end].strip(" .")
        if item:
            items.append(item)

    return items


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


def _remove_follow_up(text: str) -> str:
    cleaned = re.sub(
        r"\s+follow[- ]?up\b.*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip(" .,-")
    return cleaned


def _extract_medication_item(item: str) -> Dict[str, Optional[str]]:
    item = _remove_follow_up(item)

    strength_match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml)\b",
        item,
        flags=re.IGNORECASE,
    )

    strength = (
        f"{strength_match.group(1)} {strength_match.group(2)}"
        if strength_match
        else None
    )

    dose_match = re.search(
        r"\b(\d+(?:/\d+)?\s*(?:tablet|tablets|tab|capsule|capsules|cap|ml|drop|drops|puff|puffs))\b",
        item,
        flags=re.IGNORECASE,
    )

    dose = _clean(dose_match.group(1)) if dose_match else None

    frequency_patterns = [
        r"\b(once\s+daily)\b",
        r"\b(twice\s+daily)\b",
        r"\b(three\s+times\s+daily)\b",
        r"\b(four\s+times\s+daily)\b",
        r"\b(once\s+a\s+day)\b",
        r"\b(twice\s+a\s+day)\b",
        r"\b(three\s+times\s+a\s+day)\b",
        r"\b(OD)\b",
        r"\b(BD)\b",
        r"\b(TID)\b",
        r"\b(QID)\b",
    ]

    frequency = None

    for pattern in frequency_patterns:
        match = re.search(pattern, item, flags=re.IGNORECASE)
        if match:
            frequency = _clean(match.group(1))
            break

    timing_patterns = [
        r"\b(before\s+food)\b",
        r"\b(after\s+food)\b",
        r"\b(before\s+meals?)\b",
        r"\b(after\s+meals?)\b",
        r"\b(before\s+breakfast)\b",
        r"\b(after\s+breakfast)\b",
        r"\b(before\s+lunch)\b",
        r"\b(after\s+lunch)\b",
        r"\b(before\s+dinner)\b",
        r"\b(after\s+dinner)\b",
        r"\b(at\s+bedtime)\b",
    ]

    timing = None

    for pattern in timing_patterns:
        match = re.search(pattern, item, flags=re.IGNORECASE)
        if match:
            timing = _clean(match.group(1))
            break

    # Medicine name is the text before strength/dose/instructions.
    cut_positions = [
        match.start()
        for match in [
            strength_match,
            dose_match,
        ]
        if match is not None
    ]

    for pattern in frequency_patterns + timing_patterns:
        match = re.search(pattern, item, flags=re.IGNORECASE)
        if match:
            cut_positions.append(match.start())

    cut_at = min(cut_positions) if cut_positions else len(item)

    name = _clean(item[:cut_at]).strip(" ,-:")

    # Remove an OCR artifact such as "Rx" accidentally attached.
    name = re.sub(r"^\s*rx\s+", "", name, flags=re.IGNORECASE).strip()

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

    medications = [_extract_medication_item(item) for item in items]

    return {
        "document_type": "prescription",
        "patient_name": identity["patient_name"],
        "date": identity["date"],
        "medications": medications,
        "follow_up": _extract_follow_up(text),
    }


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
    )

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

    review_reasons = list(ocr_result.get("review_reasons") or [])
    manual_review = bool(ocr_result.get("manual_review_required", False))

    # Missing patient identity/date is not necessarily an OCR failure, but
    # it should be visible to the physician rather than silently treated
    # as complete.
    if document_type == "prescription":
        if not structured.get("medications"):
            manual_review = True
            review_reasons.append(
                "No prescription medication entries could be confidently extracted."
            )

    if document_type == "lab_report":
        if not structured.get("tests"):
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
        "document_type": structured.get("document_type", document_type),
        "patient_name": structured.get("patient_name"),
        "date": structured.get("date"),
        "structured_data": structured,
        "raw_text": raw_text,
        "ocr_confidence": ocr_result.get("mean_confidence"),
        "manual_review_required": manual_review,
        "review_reasons": list(dict.fromkeys(review_reasons)),
    }

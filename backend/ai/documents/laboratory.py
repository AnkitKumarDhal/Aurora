from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


LAB_PATTERNS = {
    "hemoglobin": [
        r"\bhemoglobin\b\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(g/dl|g/dL)?",
        r"\bhb\b\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(g/dl|g/dL)?",
    ],
    "wbc": [
        r"\b(?:wbc|white\s+blood\s+cell(?:s)?)\b\s*[:\-]?\s*"
        r"([0-9]+(?:\.[0-9]+)?)\s*"
        r"(?:/?\s*ul|x10\^3/?ul|10\^3/?ul)?",
    ],
    "platelets": [
        r"\bplatelet(?:s)?\b\s*[:\-]?\s*"
        r"([0-9]+(?:\.[0-9]+)?)\s*"
        r"(?:/?\s*ul|x10\^3/?ul|10\^3/?ul)?",
    ],
    "glucose": [
        r"\b(?:fasting\s+)?glucose\b\s*[:\-]?\s*"
        r"([0-9]+(?:\.[0-9]+)?)\s*(mg/dl|mg/dL)?",
        r"\bblood\s+sugar\b\s*[:\-]?\s*"
        r"([0-9]+(?:\.[0-9]+)?)\s*(mg/dl|mg/dL)?",
    ],
    "creatinine": [
        r"\bcreatinine\b\s*[:\-]?\s*"
        r"([0-9]+(?:\.[0-9]+)?)\s*(mg/dl|mg/dL)?",
    ],
    "hba1c": [
        # Normal OCR spelling.
        r"\b(?:hba1c|hb\s*a1c|glycated\s+hemoglobin)\b\s*[:\-]?\s*"
        r"([0-9]+(?:\.[0-9]+)?)\s*%",
        # Common OCR error: "HbAic" / "HBAic" where 1c is read as ic.
        r"\bhbaic\b\s*[:\-]?\s*"
        r"([0-9]+(?:\.[0-9]+)?)\s*%",
        # More permissive fallback for "Hb Aic".
        r"\bhb\s*aic\b\s*[:\-]?\s*"
        r"([0-9]+(?:\.[0-9]+)?)\s*%",
    ],
}

DISPLAY_NAMES = {
    "hemoglobin": "Hemoglobin",
    "wbc": "WBC",
    "platelets": "Platelets",
    "glucose": "Glucose",
    "creatinine": "Creatinine",
    "hba1c": "HbA1c",
}


def _first_nonempty(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _extract_first(
    patterns: List[str],
    text: str,
) -> Optional[Dict[str, Any]]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue

        value = match.group(1)

        unit = None
        if match.lastindex is not None and match.lastindex >= 2:
            unit = match.group(2)

        return {
            "value": float(value) if "." in value else int(value),
            "unit": unit,
            "source_text": match.group(0).strip(),
            "_match_end": match.end(),
        }

    return None


def _extract_source_range_and_flag(
    text: str,
    match_end: Optional[int],
) -> Dict[str, Any]:
    """
    Extract a reference range or explicit abnormal flag when the report
    itself supplies one close to the laboratory value.

    This function does not invent a normal range. If the source report does
    not provide a range/flag, the result remains unknown.
    """
    if match_end is None:
        return {
            "reference_range": None,
            "abnormal_flag_from_source": None,
            "abnormal_status": "unknown",
            "abnormality_basis": None,
            "requires_physician_review": False,
        }

    tail = text[match_end : match_end + 140]

    range_match = re.search(
        r"(?:reference|ref|normal)\s*(?:range)?\s*[:\-]?\s*"
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:-|to|–|—)\s*"
        r"([0-9]+(?:\.[0-9]+)?)",
        tail,
        flags=re.IGNORECASE,
    )

    if range_match is None:
        range_match = re.search(
            r"\(\s*([0-9]+(?:\.[0-9]+)?)\s*(?:-|to|–|—)\s*"
            r"([0-9]+(?:\.[0-9]+)?)\s*\)",
            tail,
            flags=re.IGNORECASE,
        )

    reference_range = None
    low = None
    high = None

    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        reference_range = f"{range_match.group(1)}-{range_match.group(2)}"

    flag_match = re.search(
        r"(?:^|\s)(high|low|abnormal|normal|H|L)(?:$|\s|[:;,)])",
        tail,
        flags=re.IGNORECASE,
    )

    source_flag = (
        flag_match.group(1)
        if flag_match
        else None
    )

    return {
        "reference_range": reference_range,
        "abnormal_flag_from_source": source_flag,
        "_range_low": low,
        "_range_high": high,
    }


def _derive_abnormal_status(
    value: Any,
    source_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Classify only when the source report gives enough evidence:
    - explicit H/L/High/Low/Abnormal/Normal flag, or
    - an explicit numeric source reference range.

    This is document-level quality screening, not a diagnosis.
    """
    raw_flag = source_context.get(
        "abnormal_flag_from_source"
    )

    if isinstance(raw_flag, str):
        flag = raw_flag.strip().lower()

        if flag in {"high", "h", "abnormal"}:
            return {
                "abnormal_status": "high_or_abnormal",
                "abnormality_basis": "source_report_flag",
                "requires_physician_review": True,
            }

        if flag in {"low", "l"}:
            return {
                "abnormal_status": "low",
                "abnormality_basis": "source_report_flag",
                "requires_physician_review": True,
            }

        if flag == "normal":
            return {
                "abnormal_status": "within_reference_range",
                "abnormality_basis": "source_report_flag",
                "requires_physician_review": False,
            }

    low = source_context.get("_range_low")
    high = source_context.get("_range_high")

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        numeric_value = None

    if (
        numeric_value is not None
        and low is not None
        and high is not None
    ):
        if numeric_value < low:
            return {
                "abnormal_status": "low",
                "abnormality_basis": "source_reference_range",
                "requires_physician_review": True,
            }

        if numeric_value > high:
            return {
                "abnormal_status": "high",
                "abnormality_basis": "source_reference_range",
                "requires_physician_review": True,
            }

        return {
            "abnormal_status": "within_reference_range",
            "abnormality_basis": "source_reference_range",
            "requires_physician_review": False,
        }

    return {
        "abnormal_status": "unknown",
        "abnormality_basis": None,
        "requires_physician_review": False,
    }


def _extract_identity(text: str) -> Dict[str, Optional[str]]:
    patient_name = None
    date = None

    name_match = re.search(
        r"\bpatient\s*[:\-]?\s*"
        r"([A-Za-z][A-Za-z .'-]{1,60}?)"
        r"(?=\s+\bdate\b|\s+\bdob\b|\s+\bage\b|$)",
        text,
        flags=re.IGNORECASE,
    )

    if name_match:
        patient_name = name_match.group(1).strip(" .:-")

    date_match = re.search(
        r"\bdate\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        text,
        flags=re.IGNORECASE,
    )

    if date_match:
        date = date_match.group(1)

    return {
        "patient_name": patient_name,
        "date": date,
    }


def extract_lab_report(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert OCR output for a laboratory report into structured,
    physician-reviewable data.

    Compatibility:
    - Accepts current OCR schema: text / mean_confidence.
    - Also accepts alias schema: raw_text / ocr_confidence.

    This module extracts document facts only. It does not diagnose disease.
    Abnormality status is classified only from an explicit source-report flag
    or a numeric reference range supplied by that same report.
    """
    if not isinstance(ocr_result, dict):
        raise TypeError("ocr_result must be a dictionary")

    raw_text = str(
        _first_nonempty(
            ocr_result.get("raw_text"),
            ocr_result.get("text"),
        )
        or ""
    ).strip()

    document_type = str(
        ocr_result.get("document_type") or ""
    ).strip().lower()

    ocr_confidence = _first_nonempty(
        ocr_result.get("ocr_confidence"),
        ocr_result.get("mean_confidence"),
    )

    identity = _extract_identity(raw_text)

    tests: List[Dict[str, Any]] = []

    for key, patterns in LAB_PATTERNS.items():
        extracted = _extract_first(patterns, raw_text)

        if extracted:
            match_end = extracted.pop("_match_end", None)
            source_context = _extract_source_range_and_flag(
                raw_text,
                match_end,
            )

            abnormal = _derive_abnormal_status(
                extracted.get("value"),
                source_context,
            )

            tests.append(
                {
                    "test": DISPLAY_NAMES[key],
                    **extracted,
                    "reference_range": source_context.get(
                        "reference_range"
                    ),
                    "abnormal_flag_from_source": source_context.get(
                        "abnormal_flag_from_source"
                    ),
                    "abnormal_status": abnormal[
                        "abnormal_status"
                    ],
                    "abnormality_basis": abnormal[
                        "abnormality_basis"
                    ],
                    "requires_physician_review": abnormal[
                        "requires_physician_review"
                    ],
                }
            )

    review_reasons: List[str] = []

    abnormal_source_tests = [
        item
        for item in tests
        if item.get("requires_physician_review") is True
    ]

    if abnormal_source_tests:
        review_reasons.append(
            f"{len(abnormal_source_tests)} laboratory result(s) were flagged by the source report or its supplied reference range and require physician review."
        )

    if document_type not in ("lab_report", ""):
        review_reasons.append(
            f"Document type was reported as '{document_type}', not lab_report."
        )

    if identity["patient_name"] is None:
        review_reasons.append("Patient name was not extracted.")

    if identity["date"] is None:
        review_reasons.append("Report date was not extracted.")

    if not tests:
        review_reasons.append(
            "No supported laboratory test values were extracted."
        )

    # Preserve OCR-stage review reasons, without duplicates.
    for reason in ocr_result.get("review_reasons") or []:
        if reason not in review_reasons:
            review_reasons.append(reason)

    manual_review_required = bool(
        ocr_result.get("manual_review_required", False)
        or review_reasons
    )

    return {
        "status": "success" if raw_text and tests else "error",
        "document_type": "lab_report",
        "patient_name": identity["patient_name"],
        "date": identity["date"],
        "structured_data": {
            "document_type": "lab_report",
            "patient_name": identity["patient_name"],
            "date": identity["date"],
            "tests": tests,
        },
        "raw_text": raw_text,
        "ocr_confidence": ocr_confidence,
        "manual_review_required": manual_review_required,
        "review_reasons": review_reasons,
    }

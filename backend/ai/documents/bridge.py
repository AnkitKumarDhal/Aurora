from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


def _ensure_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def merge_document_into_history(
    patient_history: Dict[str, Any],
    extracted_document: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Merge a structured OCR document into the clinical history without
    overwriting patient-entered information.

    Design:
    - Preserve the OCR result exactly.
    - Keep imported medication/document data separate from patient-entered data.
    - Add provenance so the physician can distinguish document-derived facts.
    - Never silently replace an existing clinical field.
    """
    updated = deepcopy(patient_history or {})
    document = deepcopy(extracted_document or {})

    document_type = document.get("document_type")
    structured = _ensure_dict(document.get("structured_data"))

    medication_history = _ensure_dict(updated.get("medication_history"))
    updated["medication_history"] = medication_history

    imports = medication_history.setdefault("document_imports", [])
    if not isinstance(imports, list):
        imports = []
        medication_history["document_imports"] = imports

    imported_record: Dict[str, Any] = {
        "document_type": document_type,
        "patient_name": document.get("patient_name") or structured.get("patient_name"),
        "date": document.get("date") or structured.get("date"),
        "source": "ocr_document",
        "ocr_confidence": document.get("ocr_confidence"),
        "manual_review_required": bool(document.get("manual_review_required", False)),
        "review_reasons": list(document.get("review_reasons") or []),
        "raw_text": document.get("raw_text"),
    }

    if document_type == "prescription":
        medications = structured.get("medications", [])
        imported_record["medications"] = deepcopy(
            medications if isinstance(medications, list) else []
        )
        imported_record["follow_up"] = structured.get("follow_up")

        # Keep a normalized list for physician review, but do not overwrite
        # patient-entered "current_medications".
        imported_medications = medication_history.setdefault(
            "document_medications", []
        )
        if not isinstance(imported_medications, list):
            imported_medications = []
            medication_history["document_medications"] = imported_medications

        for medication in imported_record["medications"]:
            if not isinstance(medication, dict):
                continue

            normalized = {
                "name": medication.get("name"),
                "strength": medication.get("strength"),
                "dose": medication.get("dose"),
                "frequency": medication.get("frequency"),
                "timing": medication.get("timing"),
                "source": "ocr_document",
                "source_document_date": imported_record["date"],
                "source_text": medication.get("source_text"),
            }
            imported_medications.append(normalized)

    imports.append(imported_record)

    return updated


def build_document_summary(extracted_document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the physician-facing document summary without changing the OCR result.
    """
    document = deepcopy(extracted_document or {})
    structured = _ensure_dict(document.get("structured_data"))

    return {
        "document_type": document.get("document_type"),
        "patient_name": document.get("patient_name") or structured.get("patient_name"),
        "date": document.get("date") or structured.get("date"),
        "ocr_confidence": document.get("ocr_confidence"),
        "manual_review_required": bool(document.get("manual_review_required", False)),
        "review_reasons": list(document.get("review_reasons") or []),
        "medications": deepcopy(structured.get("medications", [])),
        "follow_up": structured.get("follow_up"),
        "raw_text": document.get("raw_text"),
    }

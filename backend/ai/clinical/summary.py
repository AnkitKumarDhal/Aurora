from __future__ import annotations

from copy import deepcopy
from typing import Any

from backend.ai.clinical.discrepancy import detect_cross_source_discrepancies
from backend.ai.clinical.evidence import EvidenceRecord
from backend.ai.clinical.medication_safety import screen_medication_interactions
from backend.ai.clinical.timeline import build_clinical_review_panel


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _build_evidence_index(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}

    for record in records:
        field = str(record.get("field", "")).strip()

        if not field:
            continue

        index.setdefault(field, []).append(record)

    return index


def _build_evidence_panel(
    clinical_evidence: dict[str, Any],
    history: dict[str, Any],
    triage: dict[str, Any],
) -> dict[str, Any]:
    records = _as_list(clinical_evidence.get("records"))
    evidence_index = _build_evidence_index(records)

    return {
        "record_count": len(records),
        "field_count": len(evidence_index),
        "records": records,
        "fields": evidence_index,
        "triage": deepcopy(triage),
        "chief_complaint": history.get("chief_complaint"),
    }


def build_physician_summary(
    clinical_summary: dict[str, Any],
    document_summaries: list[dict[str, Any]] | None = None,
    generate_ai_draft: bool = False,
) -> dict[str, Any]:
    clinical = deepcopy(clinical_summary or {})
    documents = deepcopy(document_summaries or [])

    history = _as_dict(
        clinical.get("clinical_history")
        or clinical.get("history")
    )

    clinical_evidence = _as_dict(
        clinical.get("clinical_evidence")
    )

    triage = _as_dict(
        clinical.get("triage")
    )

    medication_history = _as_dict(
        history.get("medication_history")
    )

    patient_medications = _as_list(
        medication_history.get("current_medications")
    )

    document_medications: list[Any] = []

    for document in documents:
        structured = _as_dict(
            document.get("structured_data")
        )

        document_medications.extend(
            _as_list(
                structured.get("medications")
            )
        )

    medication_safety = screen_medication_interactions(
        patient_medications + document_medications
    )

    discrepancies = detect_cross_source_discrepancies(
        clinical_history=history,
        documents=documents,
    )

    physician_review = _as_dict(
        clinical.get("physician_review")
    )

    contradictions = _as_list(
        physician_review.get("contradictions")
    )

    patient_statements = _as_list(
        clinical.get("patient_statements")
    )

    review_panel = build_clinical_review_panel(
        clinical_history=history,
        documents=documents,
        patient_statements=patient_statements,
        contradictions=contradictions,
        triage_required=bool(
            triage.get("required", False)
        ),
    )

    lab_results: list[Any] = []
    discharge_records: list[Any] = []
    follow_up: list[Any] = []

    for document in documents:
        document_type = str(
            document.get("document_type") or ""
        ).lower()

        structured = _as_dict(
            document.get("structured_data")
        )

        if document_type == "lab_report":
            lab_results.extend(
                _as_list(
                    structured.get("tests")
                )
            )

        if document_type in {
            "discharge_summary",
            "medical_record",
        }:
            discharge_records.append(
                structured
            )

        follow_up_value = structured.get("follow_up")

        if follow_up_value:
            follow_up.append(
                {
                    "instruction": follow_up_value,
                    "date": document.get("date"),
                    "document_type": document_type,
                }
            )

    evidence_records = _as_list(
        clinical_evidence.get("records")
    )

    return {
        "status": clinical.get("status", "ready"),
        "chief_complaint": (
            clinical.get("chief_complaint")
            or history.get("chief_complaint")
        ),
        "clinical_history": history,
        "documents": documents,
        "clinical_evidence": {
            "records": evidence_records,
            "count": len(evidence_records),
            "counts_by_source": clinical_evidence.get(
                "counts_by_source",
                {},
            ),
            "counts_by_status": clinical_evidence.get(
                "counts_by_status",
                {},
            ),
        },
        "evidence_panel": _build_evidence_panel(
            clinical_evidence,
            history,
            triage,
        ),
        "cross_source_discrepancies": discrepancies,
        "clinical_review_panel": review_panel,
        "medications": {
            "patient_reported": patient_medications,
            "document_derived": document_medications,
            "interaction_screening": medication_safety,
        },
        "laboratory_results": {
            "results": lab_results,
            "count": len(lab_results),
        },
        "discharge_summaries": {
            "records": discharge_records,
            "count": len(discharge_records),
        },
        "follow_up": {
            "instructions": follow_up,
            "count": len(follow_up),
        },
        "physician_review": {
            "required": bool(
                discrepancies.get(
                    "physician_review_required",
                    False,
                )
                or medication_safety.get(
                    "requires_physician_review",
                    False,
                )
                or review_panel.get(
                    "unresolved_information",
                    {},
                ).get(
                    "physician_review_required",
                    False,
                )
            ),
            "contradictions": contradictions,
            "source_discrepancies": discrepancies.get(
                "discrepancies",
                [],
            ),
            "reasons": [
                *(
                    ["Cross-source discrepancy detected"]
                    if discrepancies.get(
                        "physician_review_required",
                        False,
                    )
                    else []
                ),
                *(
                    ["Medication safety review required"]
                    if medication_safety.get(
                        "requires_physician_review",
                        False,
                    )
                    else []
                ),
            ],
        },
        "ai_draft": {
            "active": False,
            "provider": None,
            "model": None,
            "summary": None,
            "key_points": [],
        },
    }

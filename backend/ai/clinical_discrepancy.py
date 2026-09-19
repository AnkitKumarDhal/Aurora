from __future__ import annotations

from typing import Any, Dict, List


def _normalise(value: Any) -> str:
    return " ".join(
        str(value or "")
        .lower()
        .strip()
        .split()
    )


def _contains_no_medication(value: Any) -> bool:
    text = _normalise(value)

    return text in {
        "no",
        "none",
        "none reported",
        "not taking any medicines",
        "no current medicines",
        "no medications",
    }


def detect_cross_source_discrepancies(
    clinical_history: Dict[str, Any],
    documents: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compare patient-reported information with document-derived information.

    This module does NOT decide which source is correct.
    It only identifies information that should be reconciled by the physician.
    """

    discrepancies: List[Dict[str, Any]] = []

    medication_history = clinical_history.get(
        "medication_history",
        {}
    )

    if not isinstance(
        medication_history,
        dict,
    ):
        medication_history = {}

    patient_medications = medication_history.get(
        "current_medications"
    )

    document_medications: List[Dict[str, Any]] = []

    for document in documents or []:

        if not isinstance(
            document,
            dict,
        ):
            continue

        structured = document.get(
            "structured_data",
            {}
        )

        if not isinstance(
            structured,
            dict,
        ):
            structured = {}

        medications = structured.get(
            "medications",
            []
        )

        if not isinstance(
            medications,
            list,
        ):
            continue

        for medication in medications:

            if isinstance(
                medication,
                dict,
            ):
                document_medications.append(
                    {
                        **medication,
                        "source_document_type":
                            document.get(
                                "document_type"
                            ),
                        "source_document_date":
                            document.get(
                                "date"
                            ),
                    }
                )

    # --------------------------------------------------------------
    # Medication discrepancy
    # --------------------------------------------------------------

    if (
        patient_medications
        and document_medications
        and _contains_no_medication(
            patient_medications
        )
    ):

        discrepancies.append(
            {
                "field":
                    "current_medications",

                "patient_reported":
                    patient_medications,

                "document_derived":
                    document_medications,

                "type":
                    "patient_document_discrepancy",

                "status":
                    "requires_physician_review",

                "message":
                    (
                        "Patient reports no current medicines, "
                        "but medication information was found "
                        "in uploaded medical documents."
                    ),
            }
        )

    return {
        "count":
            len(discrepancies),

        "discrepancies":
            discrepancies,

        "physician_review_required":
            bool(discrepancies),
    }
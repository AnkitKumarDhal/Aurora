from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from .ai_engine import generate_ai_physician_summary
from .clinical_discrepancy import (
    detect_cross_source_discrepancies,
)
from .clinical_timeline import (
    build_clinical_review_panel,
)
from .medication_safety import screen_medication_interactions


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


# ----------------------------------------------------------------------
# Document normalization
# ----------------------------------------------------------------------

def _normalise_document(
    document: Dict[str, Any]
) -> Dict[str, Any]:
    structured = _as_dict(
        document.get("structured_data")
    )

    return {
        "document_type": str(
            document.get("document_type")
            or structured.get("document_type")
            or "unknown"
        ),

        "patient_name": (
            document.get("patient_name")
            or structured.get("patient_name")
        ),

        "date": (
            document.get("date")
            or structured.get("date")
        ),

        "ocr_confidence": (
            document.get("ocr_confidence")
            if document.get("ocr_confidence") is not None
            else document.get("mean_confidence")
        ),

        "manual_review_required": bool(
            document.get(
                "manual_review_required",
                False,
            )
        ),

        "review_reasons": list(
            document.get(
                "review_reasons"
            )
            or []
        ),

        "medications": deepcopy(
            structured.get("medications")
            if isinstance(
                structured.get("medications"),
                list,
            )
            else []
        ),

        "tests": deepcopy(
            structured.get("tests")
            if isinstance(
                structured.get("tests"),
                list,
            )
            else []
        ),

        "diagnosis": structured.get(
            "diagnosis"
        ),

        "hospital_course": structured.get(
            "hospital_course"
        ),

        "discharge_medications":
            structured.get(
                "discharge_medications"
            ),

        "follow_up": structured.get(
            "follow_up"
        ),

        "raw_text": (
            document.get("raw_text")
            if document.get("raw_text") is not None
            else document.get("text")
        ),
    }


# ----------------------------------------------------------------------
# Evidence helpers
# ----------------------------------------------------------------------

def _normalise_evidence_store(
    clinical_evidence: Any,
) -> Dict[str, Any]:

    if not isinstance(
        clinical_evidence,
        dict,
    ):
        return {
            "records": [],
            "count": 0,
            "counts_by_source": {},
            "counts_by_status": {},
        }

    records = clinical_evidence.get(
        "records"
    )

    if not isinstance(
        records,
        list,
    ):
        records = []

    return {
        "records": deepcopy(records),

        "count": clinical_evidence.get(
            "count",
            len(records),
        ),

        "counts_by_source":
            deepcopy(
                clinical_evidence.get(
                    "counts_by_source",
                    {},
                )
            ),

        "counts_by_status":
            deepcopy(
                clinical_evidence.get(
                    "counts_by_status",
                    {},
                )
            ),
    }


def _record_to_dict(
    record: Any,
) -> Dict[str, Any]:

    if isinstance(
        record,
        dict,
    ):
        return deepcopy(record)

    if hasattr(
        record,
        "to_dict",
    ):
        try:
            result = record.to_dict()

            if isinstance(
                result,
                dict,
            ):
                return deepcopy(result)

        except Exception:
            pass

    return {}


def _build_evidence_index(
    clinical_evidence: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:

    index: Dict[
        str,
        List[Dict[str, Any]]
    ] = {}

    for raw_record in (
        clinical_evidence.get(
            "records"
        )
        or []
    ):

        record = _record_to_dict(
            raw_record
        )

        if not record:
            continue

        field = str(
            record.get(
                "field"
            )
            or "unknown"
        )

        index.setdefault(
            field,
            []
        ).append(
            record
        )

    return index


def _build_evidence_panel(
    clinical_evidence: Dict[str, Any],
    history: Dict[str, Any],
    triage: Dict[str, Any],
    contradictions: List[Any],
) -> Dict[str, Any]:

    evidence_index = _build_evidence_index(
        clinical_evidence
    )

    safety_fields = [
        "character",
        "radiation",
        "associated_symptoms",
        "aggravating_factors",
        "relieving_factors",
        "severity",
        "breathing_difficulty",
        "weakness",
        "numbness",
        "vision",
        "loss_of_consciousness",
    ]

    triage_inputs: List[Dict[str, Any]] = []

    for field in safety_fields:

        for record in evidence_index.get(
            field,
            [],
        ):

            triage_inputs.append(
                {
                    "field": field,

                    "value":
                        deepcopy(
                            record.get(
                                "value"
                            )
                        ),

                    "patient_statement":
                        record.get(
                            "evidence_text"
                        ),

                    "evidence_id":
                        record.get(
                            "evidence_id"
                        ),

                    "source_type":
                        record.get(
                            "source_type"
                        ),

                    "extraction_method":
                        record.get(
                            "extraction_method"
                        ),

                    "confidence":
                        record.get(
                            "confidence"
                        ),

                    "status":
                        record.get(
                            "status"
                        ),
                }
            )

    structured_fields = 0
    evidenced_fields = 0

    for section_name, section_value in history.items():

        if not isinstance(
            section_value,
            dict,
        ):
            continue

        for field, value in section_value.items():

            if value in (
                None,
                "",
                [],
                {},
            ):
                continue

            structured_fields += 1

            if evidence_index.get(
                field
            ):
                evidenced_fields += 1

    contradiction_evidence = []

    for raw_record in (
        clinical_evidence.get(
            "records"
        )
        or []
    ):

        record = _record_to_dict(
            raw_record
        )

        if (
            record.get(
                "source_type"
            )
            == "contradiction"
        ):
            contradiction_evidence.append(
                record
            )

    return {
        "by_field":
            deepcopy(
                evidence_index
            ),

        "triage_inputs":
            triage_inputs,

        "contradictions":
            contradiction_evidence,

        "physician_review_contradictions":
            deepcopy(
                contradictions
            ),

        "coverage":
            {
                "structured_fields":
                    structured_fields,

                "fields_with_evidence":
                    evidenced_fields,

                "coverage_fraction":
                    (
                        evidenced_fields
                        / structured_fields
                        if structured_fields
                        else 1.0
                    ),
            },

        "ledger_counts":
            {
                "count":
                    clinical_evidence.get(
                        "count",
                        0,
                    ),

                "by_source":
                    deepcopy(
                        clinical_evidence.get(
                            "counts_by_source",
                            {},
                        )
                    ),

                "by_status":
                    deepcopy(
                        clinical_evidence.get(
                            "counts_by_status",
                            {},
                        )
                    ),
            },

        "triage_required":
            bool(
                triage.get(
                    "required",
                    False,
                )
            ),

        "traceability_rule":
            (
                "Structured clinical facts remain traceable "
                "to their underlying evidence. Evidence does "
                "not constitute an autonomous diagnosis."
            ),
    }


# ----------------------------------------------------------------------
# Main physician summary
# ----------------------------------------------------------------------

def build_physician_summary(
    clinical_summary: Dict[str, Any],
    document_summaries: Optional[
        List[Dict[str, Any]]
    ] = None,
    generate_ai_draft: bool = True,
) -> Dict[str, Any]:
    """
    Build one physician-facing clinical summary from:

    1. Patient interview
    2. Clinical evidence ledger
    3. OCR medical documents
    4. Cross-source discrepancy detection
    5. Clinical timeline
    6. Unresolved-information review
    7. Optional AI narrative draft

    No autonomous diagnosis is performed here.
    """

    clinical = deepcopy(
        clinical_summary or {}
    )

    documents = deepcopy(
        document_summaries or []
    )

    history = _as_dict(
        clinical.get(
            "clinical_history"
        )
        or clinical.get(
            "history"
        )
    )

    # --------------------------------------------------------------
    # Evidence ledger
    # --------------------------------------------------------------

    clinical_evidence = (
        _normalise_evidence_store(
            clinical.get(
                "clinical_evidence"
            )
        )
    )

    # --------------------------------------------------------------
    # Document aggregation
    # --------------------------------------------------------------

    physician_documents: List[
        Dict[str, Any]
    ] = []

    document_medications: List[
        Dict[str, Any]
    ] = []

    lab_results: List[
        Dict[str, Any]
    ] = []

    discharge_records: List[
        Dict[str, Any]
    ] = []

    follow_ups: List[
        Dict[str, Any]
    ] = []

    document_review_required = False

    document_review_reasons: List[
        str
    ] = []

    for raw_document in documents:

        if not isinstance(
            raw_document,
            dict,
        ):
            continue

        document = _normalise_document(
            raw_document
        )

        normalized = {
            "document_type":
                document[
                    "document_type"
                ],

            "patient_name":
                document[
                    "patient_name"
                ],

            "date":
                document[
                    "date"
                ],

            "ocr_confidence":
                document[
                    "ocr_confidence"
                ],

            "manual_review_required":
                document[
                    "manual_review_required"
                ],

            "review_reasons":
                list(
                    document[
                        "review_reasons"
                    ]
                ),

            "medications":
                deepcopy(
                    document[
                        "medications"
                    ]
                ),

            "tests":
                deepcopy(
                    document[
                        "tests"
                    ]
                ),

            "diagnosis":
                document[
                    "diagnosis"
                ],

            "hospital_course":
                document[
                    "hospital_course"
                ],

            "discharge_medications":
                document[
                    "discharge_medications"
                ],

            "follow_up":
                document[
                    "follow_up"
                ],

            "raw_text":
                document[
                    "raw_text"
                ],
        }

        physician_documents.append(
            normalized
        )

        if document[
            "manual_review_required"
        ]:
            document_review_required = True

        for reason in document[
            "review_reasons"
        ]:

            if reason not in document_review_reasons:
                document_review_reasons.append(
                    reason
                )

        # ----------------------------------------------------------
        # Document medications
        # ----------------------------------------------------------

        for medication in document[
            "medications"
        ]:

            if not isinstance(
                medication,
                dict,
            ):
                continue

            document_medications.append(
                {
                    "name":
                        medication.get(
                            "name"
                        ),

                    "strength":
                        medication.get(
                            "strength"
                        ),

                    "dose":
                        medication.get(
                            "dose"
                        ),

                    "frequency":
                        medication.get(
                            "frequency"
                        ),

                    "timing":
                        medication.get(
                            "timing"
                        ),

                    "source":
                        "ocr_document",

                    "source_document_date":
                        document[
                            "date"
                        ],

                    "source_document_type":
                        document[
                            "document_type"
                        ],

                    "source_text":
                        medication.get(
                            "source_text"
                        ),
                }
            )

        # ----------------------------------------------------------
        # Discharge summary
        # ----------------------------------------------------------

        if (
            document[
                "document_type"
            ]
            == "discharge_summary"
        ):

            discharge_records.append(
                {
                    "patient_name":
                        document[
                            "patient_name"
                        ],

                    "date":
                        document[
                            "date"
                        ],

                    "diagnosis":
                        document[
                            "diagnosis"
                        ],

                    "hospital_course":
                        document[
                            "hospital_course"
                        ],

                    "discharge_medications":
                        document[
                            "discharge_medications"
                        ],

                    "follow_up":
                        document[
                            "follow_up"
                        ],

                    "ocr_confidence":
                        document[
                            "ocr_confidence"
                        ],

                    "manual_review_required":
                        document[
                            "manual_review_required"
                        ],

                    "review_reasons":
                        list(
                            document[
                                "review_reasons"
                            ]
                        ),

                    "source":
                        "ocr_document",
                }
            )

        # ----------------------------------------------------------
        # Laboratory results
        # ----------------------------------------------------------

        for test in document[
            "tests"
        ]:

            if not isinstance(
                test,
                dict,
            ):
                continue

            lab_results.append(
                {
                    "test":
                        test.get(
                            "test"
                        ),

                    "value":
                        test.get(
                            "value"
                        ),

                    "unit":
                        test.get(
                            "unit"
                        ),

                    "reference_range":
                        test.get(
                            "reference_range"
                        ),

                    "abnormal_flag_from_source":
                        test.get(
                            "abnormal_flag_from_source"
                        ),

                    "source":
                        "ocr_document",

                    "source_document_date":
                        document[
                            "date"
                        ],

                    "source_document_type":
                        document[
                            "document_type"
                        ],

                    "source_text":
                        test.get(
                            "source_text"
                        ),
                }
            )

        # ----------------------------------------------------------
        # Follow-up
        # ----------------------------------------------------------

        if document[
            "follow_up"
        ]:

            follow_ups.append(
                {
                    "instruction":
                        document[
                            "follow_up"
                        ],

                    "date":
                        document[
                            "date"
                        ],

                    "document_type":
                        document[
                            "document_type"
                        ],

                    "source":
                        "ocr_document",
                }
            )

    # --------------------------------------------------------------
    # Medication history
    # --------------------------------------------------------------

    medication_history = _as_dict(
        history.get(
            "medication_history"
        )
    )

    existing_document_medications = _as_list(
        medication_history.get(
            "document_medications"
        )
    )

    visible_document_medications = deepcopy(
        existing_document_medications
        if existing_document_medications
        else document_medications
    )

    structured_patient_medications = _as_list(
        medication_history.get(
            "structured_medications"
        )
    )

    interaction_inputs = list(
        structured_patient_medications
    ) + list(
        visible_document_medications
    )

    medication_safety = screen_medication_interactions(
        interaction_inputs
    )

    medication_section = {
        "patient_reported":
            medication_history.get(
                "current_medications"
            ),

        "allergies":
            medication_history.get(
                "allergies"
            ),

        "document_derived":
            visible_document_medications,

        "interaction_screening":
            medication_safety,
    }

    # --------------------------------------------------------------
    # Triage
    # --------------------------------------------------------------

    triage = clinical.get(
        "triage"
    )

    if not isinstance(
        triage,
        dict,
    ):

        triage = {
            "required":
                bool(
                    clinical.get(
                        "triage_required",
                        False,
                    )
                ),

            "red_flags":
                list(
                    clinical.get(
                        "red_flags"
                    )
                    or []
                ),
        }

    # --------------------------------------------------------------
    # Physician review
    # --------------------------------------------------------------

    physician_review = clinical.get(
        "physician_review"
    )

    if not isinstance(
        physician_review,
        dict,
    ):

        physician_review = {
            "required":
                bool(
                    clinical.get(
                        "physician_review_required",
                        False,
                    )
                ),

            "contradictions":
                list(
                    clinical.get(
                        "contradictions"
                    )
                    or []
                ),
        }

    # --------------------------------------------------------------
    # Cross-source discrepancy detection
    # --------------------------------------------------------------

    cross_source_discrepancies = (
        detect_cross_source_discrepancies(
            clinical_history=history,
            documents=documents,
        )
    )

    # --------------------------------------------------------------
    # Timeline + unresolved information
    # --------------------------------------------------------------

    patient_statements = deepcopy(
        clinical.get(
            "patient_statements"
        )
        or clinical.get(
            "raw_responses"
        )
        or []
    )

    clinical_review_panel = (
        build_clinical_review_panel(
            clinical_history=history,
            documents=documents,
            patient_statements=patient_statements,
            contradictions=(
                physician_review.get(
                    "contradictions"
                )
                or []
            ),
            triage_required=bool(
                triage.get(
                    "required",
                    False,
                )
            ),
        )
    )

    # --------------------------------------------------------------
    # Review reasons
    # --------------------------------------------------------------

    review_reasons: List[
        str
    ] = []

    if medication_safety.get(
        "requires_physician_review"
    ):
        review_reasons.append(
            "One or more supported medication-interaction rules require physician/pharmacist review."
        )

    if physician_review.get(
        "contradictions"
    ):

        review_reasons.append(
            "Clinical history contains contradictions."
        )

    if cross_source_discrepancies.get(
        "physician_review_required"
    ):

        review_reasons.append(
            "Patient-reported and document-derived "
            "information requires reconciliation."
        )

    if clinical_review_panel[
        "unresolved_information"
    ].get(
        "document_review_count",
        0,
    ) > 0:

        review_reasons.append(
            "One or more medical documents require review."
        )

    for reason in (
        document_review_reasons
    ):

        message = (
            f"Document review: {reason}"
        )

        if message not in review_reasons:
            review_reasons.append(
                message
            )

    final_review_required = bool(
        physician_review.get(
            "required",
            False,
        )

        or document_review_required

        or cross_source_discrepancies.get(
            "physician_review_required",
            False,
        )

        or medication_safety.get(
            "requires_physician_review",
            False,
        )

        or clinical_review_panel[
            "unresolved_information"
        ].get(
            "physician_review_required",
            False,
        )
    )

    # --------------------------------------------------------------
    # Laboratory section
    # --------------------------------------------------------------

    abnormal_lab_results = [
        result
        for result in lab_results
        if result.get("abnormal_status")
        in {"high", "low", "high_or_abnormal"}
    ]

    laboratory_section = {
        "results":
            lab_results,

        "abnormal_results":
            abnormal_lab_results,

        "abnormal_result_count":
            len(abnormal_lab_results),

        "documents_with_lab_results":
            [
                {
                    "patient_name":
                        item[
                            "patient_name"
                        ],

                    "date":
                        item[
                            "date"
                        ],

                    "ocr_confidence":
                        item[
                            "ocr_confidence"
                        ],

                    "manual_review_required":
                        item[
                            "manual_review_required"
                        ],

                    "review_reasons":
                        item[
                            "review_reasons"
                        ],
                }

                for item in physician_documents

                if item[
                    "document_type"
                ]
                == "lab_report"
            ],
    }

    # --------------------------------------------------------------
    # Discharge section
    # --------------------------------------------------------------

    discharge_section = {
        "records":
            discharge_records,

        "count":
            len(
                discharge_records
            ),
    }

    # --------------------------------------------------------------
    # Follow-up section
    # --------------------------------------------------------------

    follow_up_section = {
        "instructions":
            follow_ups,

        "count":
            len(
                follow_ups
            ),
    }

    # --------------------------------------------------------------
    # Physician review section
    # --------------------------------------------------------------

    physician_review_section = {
        "required":
            final_review_required,

        "triage_required":
            bool(
                triage.get(
                    "required",
                    False,
                )
            ),

        "attention_required":
            bool(
                triage.get(
                    "required",
                    False,
                )
                or final_review_required
            ),

        "contradictions":
            deepcopy(
                physician_review.get(
                    "contradictions"
                )
                or []
            ),

        "source_discrepancies":
            deepcopy(
                cross_source_discrepancies.get(
                    "discrepancies"
                )
                or []
            ),

        "reasons":
            review_reasons,

        "ai_safety_flags":
            deepcopy(
                clinical.get(
                    "ai_safety_flags"
                )
                or []
            ),

        "unresolved_information_count":
            clinical_review_panel[
                "unresolved_information"
            ].get(
                "missing_count",
                0,
            ),
    }

    # --------------------------------------------------------------
    # Core identifiers
    # --------------------------------------------------------------

    status = clinical.get(
        "status",
        "in_progress",
    )

    chief_complaint = (
        clinical.get(
            "chief_complaint"
        )
        or history.get(
            "chief_complaint"
        )
    )

    # --------------------------------------------------------------
    # Evidence panel
    # --------------------------------------------------------------

    evidence_panel = _build_evidence_panel(
        clinical_evidence=clinical_evidence,
        history=history,
        triage=triage,
        contradictions=(
            physician_review_section[
                "contradictions"
            ]
        ),
    )

    # --------------------------------------------------------------
    # Main summary
    # --------------------------------------------------------------

    summary = {
        "status":
            status,

        "chief_complaint":
            chief_complaint,

        "clinical_history":
            history,

        "history_of_present_illness":
            history.get(
                "history_of_present_illness",
                {},
            ),

        "triage":
            deepcopy(
                triage
            ),

        "physician_review":
            physician_review_section,

        "medications":
            medication_section,

        "laboratory_results":
            laboratory_section,

        "discharge_summaries":
            discharge_section,

        "follow_up":
            follow_up_section,

        "documents":
            physician_documents,

        "patient_statements":
            patient_statements,

        "raw_responses":
            deepcopy(
                clinical.get(
                    "raw_responses"
                )
                or []
            ),

        "field_history":
            deepcopy(
                clinical.get(
                    "field_history"
                )
                or {}
            ),

        "adaptive_extractions":
            deepcopy(
                clinical.get(
                    "adaptive_extractions"
                )
                or []
            ),

        "clinical_evidence":
            deepcopy(
                clinical_evidence
            ),

        "evidence_panel":
            evidence_panel,

        # NEW:
        # Chronological patient/document history + missing/review items.
        "clinical_review_panel":
            clinical_review_panel,

        # NEW:
        # Explicit reconciliation between patient statements and documents.
        "cross_source_discrepancies":
            cross_source_discrepancies,

        "ai_safety_flags":
            deepcopy(
                clinical.get(
                    "ai_safety_flags"
                )
                or []
            ),
    }

    # --------------------------------------------------------------
    # Optional AI physician draft
    # --------------------------------------------------------------

    ai_draft = None

    if generate_ai_draft:

        ai_input = {
            "status":
                status,

            "chief_complaint":
                chief_complaint,

            "history_of_present_illness":
                history.get(
                    "history_of_present_illness",
                    {},
                ),

            "respiratory_history":
                history.get(
                    "respiratory_history",
                    {},
                ),

            "gastrointestinal_history":
                history.get(
                    "gastrointestinal_history",
                    {},
                ),

            "neurological_history":
                history.get(
                    "neurological_history",
                    {},
                ),

            "skin_history":
                history.get(
                    "skin_history",
                    {},
                ),

            "urinary_history":
                history.get(
                    "urinary_history",
                    {},
                ),

            "past_history":
                history.get(
                    "past_history",
                    {},
                ),

            "medication_history":
                history.get(
                    "medication_history",
                    {},
                ),

            "family_history":
                history.get(
                    "family_history",
                    {},
                ),

            "personal_history":
                history.get(
                    "personal_history",
                    {},
                ),

            "review_of_systems":
                history.get(
                    "review_of_systems",
                    {},
                ),

            "ayush":
                history.get(
                    "ayush",
                    {},
                ),

            "triage":
                deepcopy(
                    triage
                ),

            "physician_review":
                deepcopy(
                    physician_review_section
                ),

            "medications":
                deepcopy(
                    medication_section
                ),

            "laboratory_results":
                deepcopy(
                    laboratory_section
                ),

            "discharge_summaries":
                deepcopy(
                    discharge_section
                ),

            "follow_up":
                deepcopy(
                    follow_up_section
                ),

            "documents":
                [
                    {
                        "document_type":
                            item.get(
                                "document_type"
                            ),

                        "date":
                            item.get(
                                "date"
                            ),

                        "manual_review_required":
                            item.get(
                                "manual_review_required"
                            ),

                        "review_reasons":
                            item.get(
                                "review_reasons",
                                [],
                            ),
                    }

                    for item in physician_documents
                ],

            "clinical_evidence":
                deepcopy(
                    clinical_evidence
                ),

            "evidence_panel":
                deepcopy(
                    evidence_panel
                ),

            "clinical_review_panel":
                deepcopy(
                    clinical_review_panel
                ),

            "cross_source_discrepancies":
                deepcopy(
                    cross_source_discrepancies
                ),
        }

        ai_draft = (
            generate_ai_physician_summary(
                ai_input
            )
        )

    summary["ai_draft"] = (
        {
            "active":
                True,

            **ai_draft,
        }

        if isinstance(
            ai_draft,
            dict,
        )

        else {
            "active":
                False,

            "provider":
                None,

            "model":
                None,

            "summary":
                None,

            "key_points":
                [],
        }
    )

    return summary
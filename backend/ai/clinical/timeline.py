from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional


# ============================================================================
# DEFAULT CLINICAL FIELDS
# ============================================================================

DEFAULT_RELEVANT_FIELDS = [
    "history_of_present_illness.onset",
    "history_of_present_illness.site",
    "history_of_present_illness.character",
    "history_of_present_illness.radiation",
    "history_of_present_illness.associated_symptoms",
    "history_of_present_illness.timing",
    "history_of_present_illness.aggravating_factors",
    "history_of_present_illness.relieving_factors",
    "history_of_present_illness.severity",
    "history_of_present_illness.general_complaint",
    "past_history.medical_history",
    "past_history.surgical_history",
    "medication_history.current_medications",
    "medication_history.allergies",
    "family_history.family_history",
    "personal_history.diet",
    "personal_history.sleep",
    "personal_history.smoking",
    "personal_history.alcohol",
    "personal_history.activity",
]


# ============================================================================
# HELPERS
# ============================================================================

def _safe_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _to_date(value: Any) -> Optional[date]:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()

    if not text:
        return None

    formats = (
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%y",
        "%d-%m-%y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None


def _normalize_date(value: Any) -> Optional[str]:
    parsed = _to_date(value)

    if parsed is None:
        return None

    return parsed.isoformat()


def _date_sort_key(value: Any) -> tuple:
    parsed = _to_date(value)

    if parsed is None:
        return (1, date.max)

    return (0, parsed)


def _has_meaningful_value(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0

    return True


def _get_nested_value(
    data: Dict[str, Any],
    path: str,
) -> Any:
    current: Any = data

    for part in path.split("."):
        if not isinstance(current, dict):
            return None

        current = current.get(part)

    return current


def _field_name(path: str) -> str:
    return path.split(".")[-1]


def _section_name(path: str) -> str:
    parts = path.split(".")

    if len(parts) >= 2:
        return parts[0]

    return "clinical_history"


def _document_type(
    document: Dict[str, Any],
) -> str:
    return str(
        document.get("document_type")
        or document.get("type")
        or document.get("document_name")
        or "document"
    )


# ============================================================================
# CLINICAL TIMELINE
# ============================================================================

def build_clinical_timeline(
    documents: Optional[Iterable[Dict[str, Any]]] = None,
    clinical_history: Optional[Dict[str, Any]] = None,
    patient_statements: Optional[Iterable[Any]] = None,
) -> Dict[str, Any]:

    documents = list(documents or [])
    patient_statements = list(patient_statements or [])
    clinical_history = _safe_dict(clinical_history)

    events: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Current encounter
    #
    # IMPORTANT:
    # Do NOT create a synthetic encounter merely because clinical_history
    # exists. An encounter belongs on the timeline only when an actual
    # encounter/visit/date value is available.
    # ------------------------------------------------------------------

    encounter_date = (
        clinical_history.get("encounter_date")
        or clinical_history.get("visit_date")
        or clinical_history.get("date")
    )

    if encounter_date is not None:
        events.append(
            {
                "date": _normalize_date(encounter_date),
                "event_type": "current_encounter",
                "source": "clinical_history",
                "source_type": "clinical_history",
                "label": "Current clinical encounter",
                "details": clinical_history,
            }
        )

    # ------------------------------------------------------------------
    # Patient statements
    # ------------------------------------------------------------------

    for index, statement in enumerate(
        patient_statements,
        start=0,
    ):

        if isinstance(statement, dict):

            statement_date = (
                statement.get("date")
                or statement.get("timestamp")
                or statement.get("recorded_at")
            )

            field = statement.get("field")

            response = (
                statement.get("patient_response")
                or statement.get("statement")
                or statement.get("text")
                or statement.get("response")
                or statement.get("value")
            )

            if field:
                label = (
                    "Patient statement - "
                    + str(field)
                )
            else:
                label = "Patient statement"

            events.append(
                {
                    "date": _normalize_date(
                        statement_date
                    ),
                    "event_type": "patient_statement",
                    "source": "patient_statement",
                    "source_type": "patient_statement",
                    "label": label,
                    "field": field,
                    "statement": response,
                    "patient_response": response,
                    "raw": statement,
                    "index": statement.get(
                        "index",
                        index,
                    ),
                }
            )

        else:

            events.append(
                {
                    "date": None,
                    "event_type": "patient_statement",
                    "source": "patient_statement",
                    "source_type": "patient_statement",
                    "label": "Patient statement",
                    "field": None,
                    "statement": str(statement),
                    "patient_response": str(statement),
                    "raw": statement,
                    "index": index,
                }
            )

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    for index, document in enumerate(
        documents,
        start=0,
    ):

        document = _safe_dict(document)

        document_type = _document_type(
            document
        )

        document_date = (
            document.get("date")
            or document.get("document_date")
            or document.get("visit_date")
        )

        structured_data = (
            document.get("structured_data")
            or document.get("extracted_data")
            or document.get("data")
            or {}
        )

        events.append(
            {
                "date": _normalize_date(
                    document_date
                ),

                # Existing API contract:
                # prescription / lab_report / discharge_summary
                "event_type": document_type,

                "source": "ocr_document",
                "source_type": "ocr_document",

                "label": document_type,
                "document_type": document_type,

                "structured_data": structured_data,

                "patient_name":
                    document.get("patient_name"),

                "ocr_confidence":
                    document.get("ocr_confidence"),

                "manual_review_required":
                    bool(
                        document.get(
                            "manual_review_required",
                            False,
                        )
                    ),

                "review_reasons":
                    list(
                        document.get(
                            "review_reasons"
                        )
                        or []
                    ),

                "raw": document,

                "document_index": index,
            }
        )

    # ------------------------------------------------------------------
    # Chronological ordering
    # ------------------------------------------------------------------

    events.sort(
        key=lambda event: (
            _date_sort_key(
                event.get("date")
            ),
            event.get(
                "index",
                event.get(
                    "document_index",
                    0,
                ),
            ),
        )
    )

    dated_events = [
        event
        for event in events
        if event.get("date") is not None
    ]

    undated_events = [
        event
        for event in events
        if event.get("date") is None
    ]

    source_counts: Dict[str, int] = {}

    for event in events:
        source = event.get(
            "source",
            "unknown",
        )

        source_counts[source] = (
            source_counts.get(
                source,
                0,
            )
            + 1
        )

    date_range = None

    if dated_events:

        dates = [
            _to_date(
                event.get("date")
            )
            for event in dated_events
        ]

        dates = [
            value
            for value in dates
            if value is not None
        ]

        if dates:
            date_range = {
                "start": min(dates).isoformat(),
                "end": max(dates).isoformat(),
            }

    return {
        "count": len(events),
        "events": events,
        "dated_count": len(dated_events),
        "undated_count": len(undated_events),
        "date_range": date_range,
        "source_counts": source_counts,
    }


# ============================================================================
# UNRESOLVED INFORMATION
# ============================================================================

def build_unresolved_information(
    clinical_history: Optional[Dict[str, Any]] = None,
    documents: Optional[Iterable[Dict[str, Any]]] = None,
    contradictions: Optional[Iterable[Any]] = None,
    triage_required: bool = False,
    relevant_fields: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:

    clinical_history = _safe_dict(
        clinical_history
    )

    documents = list(
        documents or []
    )

    contradictions = list(
        contradictions or []
    )

    fields = list(
        relevant_fields
        if relevant_fields is not None
        else DEFAULT_RELEVANT_FIELDS
    )

    # ------------------------------------------------------------------
    # Missing information
    # ------------------------------------------------------------------

    missing_information: List[
        Dict[str, Any]
    ] = []

    for path in fields:

        value = _get_nested_value(
            clinical_history,
            path,
        )

        if not _has_meaningful_value(value):

            missing_information.append(
                {
                    "field":
                        _field_name(path),

                    "section":
                        _section_name(path),

                    "path":
                        path,

                    "status":
                        "missing",

                    "message":
                        (
                            "Information has not "
                            "been provided."
                        ),
                }
            )

    # ------------------------------------------------------------------
    # Contradictions
    # ------------------------------------------------------------------

    contradiction_items: List[
        Dict[str, Any]
    ] = []

    for contradiction in contradictions:

        if isinstance(
            contradiction,
            dict,
        ):

            contradiction_items.append(
                dict(contradiction)
            )

        else:

            contradiction_items.append(
                {
                    "description":
                        str(contradiction)
                }
            )

    # ------------------------------------------------------------------
    # Documents requiring review
    # ------------------------------------------------------------------

    document_review_items: List[
        Dict[str, Any]
    ] = []

    for document in documents:

        document = _safe_dict(
            document
        )

        if document.get(
            "manual_review_required"
        ) is True:

            document_review_items.append(
                {
                    "document_type":
                        _document_type(
                            document
                        ),

                    "date":
                        _normalize_date(
                            document.get(
                                "date"
                            )
                        ),

                    "reasons":
                        list(
                            document.get(
                                "review_reasons"
                            )
                            or []
                        ),
                }
            )

    # ------------------------------------------------------------------
    # Priority attention
    # ------------------------------------------------------------------

    attention_items: List[
        Dict[str, Any]
    ] = []

    if triage_required:

        attention_items.append(
            {
                "type": "triage",
                "priority": "high",
                "message": (
                    "Clinical history contains "
                    "red-flag information requiring "
                    "prompt physician assessment."
                ),
            }
        )

    for contradiction in contradiction_items:

        attention_items.append(
            {
                "type":
                    "contradiction",

                "priority":
                    "high",

                "details":
                    contradiction,
            }
        )

    for review_item in document_review_items:

        attention_items.append(
            {
                "type":
                    "document_review",

                "priority":
                    "high",

                "details":
                    review_item,
            }
        )

    attention_count = len(
        attention_items
    )

    priority_attention_required = (
        attention_count > 0
    )

    physician_review_required = (
        attention_count > 0
    )

    return {
        # Existing API contract.
        "missing_information":
            missing_information,

        "missing_count":
            len(
                missing_information
            ),

        "physician_review_required":
            physician_review_required,

        "priority_attention_required":
            priority_attention_required,

        "attention_count":
            attention_count,

        # Compatibility aliases.
        "missing_fields":
            [
                item["field"]
                for item in missing_information
            ],

        "unresolved_count":
            len(
                missing_information
            ),

        "count":
            len(
                missing_information
            ),

        "contradictions":
            contradiction_items,

        "contradiction_count":
            len(
                contradiction_items
            ),

        "document_review_items":
            document_review_items,

        "document_review_count":
            len(
                document_review_items
            ),

        "attention_items":
            attention_items,

        "requires_attention":
            priority_attention_required,

        "attention_required":
            priority_attention_required,

        "priority_attention":
            attention_items,
    }


# ============================================================================
# UNIFIED CLINICAL REVIEW PANEL
# ============================================================================

def build_clinical_review_panel(
    clinical_history: Optional[Dict[str, Any]] = None,
    documents: Optional[Iterable[Dict[str, Any]]] = None,
    patient_statements: Optional[Iterable[Any]] = None,
    contradictions: Optional[Iterable[Any]] = None,
    triage_required: bool = False,
    relevant_fields: Optional[Iterable[str]] = None,
    summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    documents = list(
        documents or []
    )

    patient_statements = list(
        patient_statements or []
    )

    contradictions = list(
        contradictions or []
    )

    timeline = build_clinical_timeline(
        documents=documents,
        clinical_history=clinical_history,
        patient_statements=patient_statements,
    )

    unresolved_information = (
        build_unresolved_information(
            clinical_history=clinical_history,
            documents=documents,
            contradictions=contradictions,
            triage_required=triage_required,
            relevant_fields=relevant_fields,
        )
    )

    panel: Dict[str, Any] = {
        "timeline":
            timeline,

        "unresolved_information":
            unresolved_information,
    }

    if summary is not None:
        panel["summary"] = summary

    return panel


__all__ = [
    "DEFAULT_RELEVANT_FIELDS",
    "build_clinical_timeline",
    "build_unresolved_information",
    "build_clinical_review_panel",
]
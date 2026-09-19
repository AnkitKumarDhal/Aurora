from __future__ import annotations

"""
Aurora integration boundary for MediKiosk clinical intelligence.

This module deliberately does NOT own:
- patient/session persistence
- conversation persistence
- queue management
- triage scoring
- doctor assignment
- promotion

Aurora remains the system of record.

The adapter is stateless. Each call receives an Aurora session_id and the
patient turns already persisted by Aurora. A fresh ClinicalSession is rebuilt
by replaying those patient turns. This keeps the clinical engine compatible
with Aurora's persistent session architecture without maintaining a second
in-memory session registry.
"""

from copy import deepcopy
from datetime import datetime, timezone
import json
from typing import Any, Dict, Iterable, List, Optional
from uuid import NAMESPACE_URL, uuid5

from .clinical_service import ClinicalSession
from .physician_summary import build_physician_summary


# ---------------------------------------------------------------------------
# Aurora enum values copied as strings intentionally.
# The adapter must remain importable without depending on Aurora's Python
# package layout.
# ---------------------------------------------------------------------------

SIGNAL_TYPES = {
    "ALLERGY",
    "DURATION",
    "HISTORY",
    "MEDICATION",
    "OTHER",
    "RED_FLAG",
    "SYMPTOM",
    "VITAL",
}


class AuroraClinicalAdapter:
    """
    Stateless integration boundary between MediKiosk and Aurora.

    Public methods:
        process_turn(...)
        extract_signals(...)
        generate_summary(...)
        finalize_clinical_session(...)
    """

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process_turn(
        self,
        session_id: str,
        patient_text: str,
        previous_patient_turns: Optional[Iterable[Any]] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process one new patient turn.

        `previous_patient_turns` must contain turns already persisted by
        Aurora and must NOT contain the new `patient_text`.
        """
        if not str(session_id).strip():
            raise ValueError("session_id is required")

        if not str(patient_text).strip():
            raise ValueError("patient_text is required")

        session = self._rebuild_session(
            previous_patient_turns or [],
        )

        result = session.process_response(
            str(patient_text),
        )

        signals = self._build_signal_records(
            session_id=session_id,
            session=session,
        )

        return {
            "session_id": session_id,
            "language": language,
            "input_type": "TEXT",
            "patient_text": str(patient_text),
            "assistant_response": result.get(
                "next_question"
            ),
            "next_question": result.get(
                "next_question"
            ),
            "field": result.get(
                "field"
            ),
            "completed": bool(
                result.get("completed", False)
            ),
            "history": deepcopy(
                session.patient_history
            ),
            "red_flags": list(
                session.red_flags
            ),
            "triage_required": bool(
                session.triage_required
            ),
            "physician_review_required": bool(
                session.review_required
            ),
            "contradictions": deepcopy(
                session.contradictions
            ),
            "clinical_evidence": session.evidence_store.to_dict(),
            "signals": signals,
        }

    def extract_signals(
        self,
        session_id: str,
        patient_turns: Iterable[Any],
        document_summaries: Optional[
            Iterable[Dict[str, Any]]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Rebuild clinical state from Aurora-persisted turns and return
        Aurora-compatible ClinicalSignal-shaped payloads.

        This method does not calculate queue priority or assign a doctor.
        """
        if not str(session_id).strip():
            raise ValueError("session_id is required")

        session = self._rebuild_session(
            patient_turns,
        )

        documents = self._normalise_documents(
            document_summaries or [],
        )

        signals = self._build_signal_records(
            session_id=session_id,
            session=session,
            documents=documents,
        )

        return {
            "session_id": session_id,
            "signals": signals,
            "red_flags": list(
                session.red_flags
            ),
            "triage_inputs": self._build_triage_inputs(
                session
            ),
            "clinical_evidence": session.evidence_store.to_dict(),
        }

    def generate_summary(
        self,
        session_id: str,
        patient_turns: Iterable[Any],
        document_summaries: Optional[
            Iterable[Dict[str, Any]]
        ] = None,
        generate_ai_draft: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a physician summary and an Aurora ClinicalSummary-shaped
        payload without persisting anything.
        """
        if not str(session_id).strip():
            raise ValueError("session_id is required")

        session = self._rebuild_session(
            patient_turns,
        )

        documents = self._normalise_documents(
            document_summaries or [],
        )

        clinical_snapshot = session.get_summary()

        physician_summary = build_physician_summary(
            clinical_summary=clinical_snapshot,
            document_summaries=documents,
            generate_ai_draft=generate_ai_draft,
        )

        signals = self._build_signal_records(
            session_id=session_id,
            session=session,
            documents=documents,
        )

        aurora_summary = self._to_aurora_summary(
            session_id=session_id,
            physician_summary=physician_summary,
            signals=signals,
        )

        return {
            "session_id": session_id,
            "aurora_summary": aurora_summary,
            "physician_summary": physician_summary,
            "signals": signals,
            "triage_inputs": self._build_triage_inputs(
                session
            ),
            "red_flags": list(
                session.red_flags
            ),
            "triage_required": bool(
                session.triage_required
            ),
            "clinical_evidence": session.evidence_store.to_dict(),
        }

    def finalize_clinical_session(
        self,
        session_id: str,
        patient_turns: Iterable[Any],
        document_summaries: Optional[
            Iterable[Dict[str, Any]]
        ] = None,
        generate_ai_draft: bool = False,
    ) -> Dict[str, Any]:
        """
        Convenience method for Aurora's intake-finalization boundary.

        It generates all clinical outputs but deliberately does not mutate
        Aurora session/summary/triage/queue state. Aurora remains responsible
        for persisting the returned objects and running TriageService.
        """
        result = self.generate_summary(
            session_id=session_id,
            patient_turns=patient_turns,
            document_summaries=document_summaries,
            generate_ai_draft=generate_ai_draft,
        )

        result["completed"] = bool(
            result["physician_summary"].get(
                "status"
            )
            == "completed"
        )

        return result

    # ------------------------------------------------------------------
    # Session reconstruction
    # ------------------------------------------------------------------

    @staticmethod
    def _rebuild_session(
        patient_turns: Iterable[Any],
    ) -> ClinicalSession:
        """
        Reconstruct clinical state from Aurora's persisted conversation turns.

        No process-global/session-global dictionary is used.
        """
        turns = [
            turn
            for turn in (
                AuroraClinicalAdapter._normalise_turns(
                    patient_turns
                )
            )
            if turn.get("content")
        ]

        turns.sort(
            key=AuroraClinicalAdapter._turn_sort_key
        )

        session = ClinicalSession()

        for turn in turns:
            # Aurora may eventually persist system turns as well. Only
            # patient content is replayed into the clinical engine.
            speaker = str(
                turn.get("speaker", "patient")
            ).strip().lower()

            if speaker not in {
                "patient",
                "user",
            }:
                continue

            session.process_response(
                str(turn["content"]),
            )

        return session

    @staticmethod
    def _normalise_turns(
        turns: Iterable[Any],
    ) -> List[Dict[str, Any]]:
        normalised: List[Dict[str, Any]] = []

        for index, turn in enumerate(turns):
            if isinstance(turn, str):
                normalised.append(
                    {
                        "content": turn,
                        "speaker": "patient",
                        "index": index,
                    }
                )
                continue

            if not isinstance(turn, dict):
                continue

            content = (
                turn.get("content")
                or turn.get("patient_response")
                or turn.get("response")
                or turn.get("text")
            )

            if content is None:
                continue

            normalised.append(
                {
                    "content": str(content),
                    "speaker": turn.get(
                        "speaker",
                        "patient",
                    ),
                    "created_at": turn.get(
                        "created_at"
                    ),
                    "index": turn.get(
                        "index",
                        index,
                    ),
                }
            )

        return normalised

    @staticmethod
    def _turn_sort_key(
        turn: Dict[str, Any],
    ) -> tuple:
        created_at = turn.get(
            "created_at"
        )

        if created_at is None:
            return (
                1,
                "",
                turn.get("index", 0),
            )

        return (
            0,
            str(created_at),
            turn.get("index", 0),
        )

    # ------------------------------------------------------------------
    # Document normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_documents(
        documents: Iterable[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []

        for document in documents:
            if not isinstance(document, dict):
                continue

            # Support our local medical_document_pipeline output.
            if isinstance(
                document.get("structured_document"),
                dict,
            ):
                structured = document.get(
                    "structured_document"
                )

                copied = dict(document)
                copied["structured_data"] = structured
                result.append(copied)
                continue

            # Support Aurora DocumentExtraction-style payloads.
            if isinstance(
                document.get("structured_data"),
                dict,
            ):
                result.append(
                    deepcopy(document)
                )
                continue

            result.append(
                deepcopy(document)
            )

        return result

    # ------------------------------------------------------------------
    # Signal construction
    # ------------------------------------------------------------------

    def _build_signal_records(
        self,
        session_id: str,
        session: ClinicalSession,
        documents: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        signals: List[Dict[str, Any]] = []

        history = session.patient_history

        # --------------------------------------------------------------
        # Patient-derived clinical evidence
        # --------------------------------------------------------------

        evidence_records = (
            session.evidence_store.to_dict().get(
                "records",
                [],
            )
        )

        evidence_seen = set()

        for index, record in enumerate(
            evidence_records
        ):
            if not isinstance(record, dict):
                continue

            field = str(
                record.get("field")
                or ""
            ).strip()

            if not field:
                continue

            value = record.get(
                "value"
            )

            source = str(
                record.get("source_type")
                or "patient_statement"
            )

            key = self._signal_key(
                session_id,
                field,
                value,
                source,
            )

            # Keep the latest representation of an identical source/value
            # while retaining different contradictory values as separate
            # evidence signals.
            if key in evidence_seen:
                continue

            evidence_seen.add(key)

            signal_type = self._signal_type_for_field(
                field
            )

            signals.append(
                self._make_signal(
                    session_id=session_id,
                    name=field,
                    value=value,
                    signal_type=signal_type,
                    source=source,
                    confidence=record.get(
                        "confidence"
                    ),
                    ordinal=index,
                )
            )

        # Chief complaint is not necessarily an evidence-ledger field.
        chief_complaint = history.get(
            "chief_complaint"
        )

        if chief_complaint:
            signals.append(
                self._make_signal(
                    session_id=session_id,
                    name="chief_complaint",
                    value=chief_complaint,
                    signal_type="SYMPTOM",
                    source="patient_statement",
                    confidence=1.0,
                    ordinal=500,
                )
            )

        # --------------------------------------------------------------
        # Safety / triage signals
        # --------------------------------------------------------------

        for triage_signal in self._build_triage_inputs(
            session
        ):
            signals.append(
                self._make_signal(
                    session_id=session_id,
                    name=triage_signal["name"],
                    value=triage_signal["value"],
                    signal_type="RED_FLAG"
                    if triage_signal["name"]
                    in {
                        "loss_of_consciousness",
                        "severe_breathing_difficulty",
                        "stroke_symptoms",
                        "severe_chest_pain",
                        "active_severe_bleeding",
                        "suicidal_intent",
                    }
                    else "OTHER",
                    source="clinical_engine",
                    confidence=1.0,
                    ordinal=700,
                )
            )

        # --------------------------------------------------------------
        # Document-derived signals
        # --------------------------------------------------------------

        for document_index, document in enumerate(
            documents or []
        ):
            structured = document.get(
                "structured_data"
            )

            if not isinstance(
                structured,
                dict,
            ):
                continue

            document_date = document.get(
                "date"
            )

            document_type = (
                document.get("document_type")
                or structured.get("document_type")
                or "document"
            )

            medications = structured.get(
                "medications"
            )

            if isinstance(
                medications,
                list,
            ):
                for medication_index, medication in enumerate(
                    medications
                ):
                    if not isinstance(
                        medication,
                        dict,
                    ):
                        continue

                    name = medication.get(
                        "name"
                    )

                    if not name:
                        continue

                    medication_value = self._compact_document_medication(
                        medication
                    )

                    signals.append(
                        self._make_signal(
                            session_id=session_id,
                            name=f"document_medication:{name}",
                            value=medication_value,
                            signal_type="MEDICATION",
                            source="ocr_document",
                            confidence=self._document_confidence(
                                document
                            ),
                            ordinal=(
                                1000
                                + document_index * 100
                                + medication_index
                            ),
                            metadata={
                                "document_type":
                                    document_type,
                                "document_date":
                                    document_date,
                            },
                        )
                    )

            tests = structured.get(
                "tests"
            )

            if isinstance(
                tests,
                list,
            ):
                for test_index, test in enumerate(
                    tests
                ):
                    if not isinstance(
                        test,
                        dict,
                    ):
                        continue

                    test_name = test.get(
                        "test"
                    )

                    if not test_name:
                        continue

                    value = test.get(
                        "value"
                    )

                    abnormal = test.get(
                        "abnormal_flag_from_source"
                    )

                    signal_value = {
                        "value": value,
                        "unit": test.get("unit"),
                        "abnormal_flag_from_source": abnormal,
                    }

                    signals.append(
                        self._make_signal(
                            session_id=session_id,
                            name=f"lab:{test_name}",
                            value=signal_value,
                            signal_type="VITAL"
                            if abnormal is not None
                            else "OTHER",
                            source="ocr_document",
                            confidence=self._document_confidence(
                                document
                            ),
                            ordinal=(
                                2000
                                + document_index * 100
                                + test_index
                            ),
                            metadata={
                                "document_type":
                                    document_type,
                                "document_date":
                                    document_date,
                            },
                        )
                    )

        return signals

    @staticmethod
    def _signal_type_for_field(
        field: str,
    ) -> str:
        if field in {
            "allergies",
        }:
            return "ALLERGY"

        if field in {
            "current_medications",
        } or field.startswith("document_medication:"):
            return "MEDICATION"

        if field == "onset":
            return "DURATION"

        if field in {
            "medical_history",
            "surgical_history",
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
        }:
            return "HISTORY"

        if field == "severity":
            return "OTHER"

        return "SYMPTOM"

    @staticmethod
    def _document_confidence(
        document: Dict[str, Any],
    ) -> Optional[float]:
        value = document.get(
            "ocr_confidence"
        )

        if value is None:
            value = document.get(
                "mean_confidence"
            )

        if value is None:
            return None

        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None

        if numeric > 1:
            numeric /= 100.0

        return max(
            0.0,
            min(1.0, numeric),
        )

    @staticmethod
    def _compact_document_medication(
        medication: Dict[str, Any],
    ) -> str:
        pieces = []

        for key in (
            "name",
            "strength",
            "dose",
            "frequency",
            "timing",
        ):
            value = medication.get(key)
            if value:
                pieces.append(
                    str(value)
                )

        return " ".join(pieces)

    @staticmethod
    def _signal_key(
        session_id: str,
        name: str,
        value: Any,
        source: str,
    ) -> str:
        return (
            f"{session_id}|{name}|"
            f"{AuroraClinicalAdapter._json_value(value)}|{source}"
        )

    @staticmethod
    def _json_value(
        value: Any,
    ) -> str:
        try:
            return json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _make_signal(
        session_id: str,
        name: str,
        value: Any,
        signal_type: str,
        source: str,
        confidence: Optional[float],
        ordinal: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if signal_type not in SIGNAL_TYPES:
            signal_type = "OTHER"

        signal_id = str(
            uuid5(
                NAMESPACE_URL,
                (
                    f"medikiosk-aurora|{session_id}|"
                    f"{name}|{AuroraClinicalAdapter._json_value(value)}|"
                    f"{source}|{ordinal}"
                ),
            )
        )

        return {
            "signal_id": signal_id,
            "session_id": session_id,
            "signal_type": signal_type,
            "name": name,
            "value": AuroraClinicalAdapter._aurora_value(
                value
            ),
            "confidence": confidence,
            "source": source,
            "metadata": metadata or {},
        }

    @staticmethod
    def _aurora_value(
        value: Any,
    ) -> str | bool | int | float | None:
        """
        Aurora ClinicalSignal.value accepts scalar values only. Complex
        clinical values are therefore serialized as JSON strings here while
        the richer evidence remains available in the full clinical package.
        """
        if value is None or isinstance(
            value,
            (str, bool, int, float),
        ):
            return value

        return AuroraClinicalAdapter._json_value(
            value
        )

    # ------------------------------------------------------------------
    # Aurora triage hand-off
    # ------------------------------------------------------------------

    @staticmethod
    def _build_triage_inputs(
        session: ClinicalSession,
    ) -> List[Dict[str, Any]]:
        history = session.patient_history
        hpi = history.get(
            "history_of_present_illness",
            {},
        )

        inputs: List[Dict[str, Any]] = []

        severity = hpi.get(
            "severity"
        )

        try:
            severity_number = float(
                severity
            )
        except (TypeError, ValueError):
            severity_number = None

        if severity_number is not None:
            if severity_number >= 7:
                inputs.append(
                    {
                        "name": "severe_pain",
                        "value": True,
                    }
                )
            elif severity_number >= 4:
                inputs.append(
                    {
                        "name": "moderate_pain",
                        "value": True,
                    }
                )

        timing = str(
            hpi.get("timing")
            or ""
        ).lower()

        if any(
            marker in timing
            for marker in (
                "continuous",
                "constant",
                "persistent",
            )
        ):
            inputs.append(
                {
                    "name": "persistent_symptoms",
                    "value": True,
                }
            )

        # Translate the already-detected red flags into the exact signal names
        # Aurora's TriageEngine understands. Aurora still owns the actual
        # urgency/priority calculation.
        red_flags_text = " ".join(
            str(flag).lower()
            for flag in session.red_flags
        )

        red_flag_mappings = (
            (
                "loss_of_consciousness",
                (
                    "loss of consciousness",
                    "fainted",
                    "fainting",
                ),
            ),
            (
                "severe_breathing_difficulty",
                (
                    "severe breathing difficulty",
                    "difficulty breathing",
                ),
            ),
            (
                "stroke_symptoms",
                (
                    "stroke-like",
                    "stroke symptoms",
                ),
            ),
            (
                "severe_chest_pain",
                (
                    "severe chest pain",
                    "chest pain with multiple concerning features",
                ),
            ),
            (
                "active_severe_bleeding",
                (
                    "severe bleeding",
                    "active severe bleeding",
                ),
            ),
            (
                "suicidal_intent",
                (
                    "suicidal",
                    "suicidal intent",
                ),
            ),
        )

        for signal_name, markers in red_flag_mappings:
            if any(
                marker in red_flags_text
                for marker in markers
            ):
                inputs.append(
                    {
                        "name": signal_name,
                        "value": True,
                    }
                )

        # Preserve deterministic order while removing duplicates.
        seen = set()
        unique_inputs = []

        for item in inputs:
            key = (
                item["name"],
                item["value"],
            )
            if key in seen:
                continue
            seen.add(key)
            unique_inputs.append(item)

        return unique_inputs

    # ------------------------------------------------------------------
    # Aurora ClinicalSummary mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _to_aurora_summary(
        session_id: str,
        physician_summary: Dict[str, Any],
        signals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        history = physician_summary.get(
            "clinical_history"
        )
        if not isinstance(history, dict):
            history = {}

        hpi = history.get(
            "history_of_present_illness",
            {},
        )
        if not isinstance(hpi, dict):
            hpi = {}

        past = history.get(
            "past_history",
            {},
        )
        if not isinstance(past, dict):
            past = {}

        medication_history = history.get(
            "medication_history",
            {},
        )
        if not isinstance(
            medication_history,
            dict,
        ):
            medication_history = {}

        # --------------------------
        # Past medical history
        # --------------------------

        past_medical_history = []

        medical_history = past.get(
            "medical_history"
        )
        if medical_history not in (
            None,
            "",
        ):
            past_medical_history.append(
                f"Medical history: {medical_history}"
            )

        surgical_history = past.get(
            "surgical_history"
        )
        if surgical_history not in (
            None,
            "",
        ):
            past_medical_history.append(
                f"Surgical history: {surgical_history}"
            )

        # --------------------------
        # Medications
        # --------------------------

        medications: List[str] = []

        patient_medications = medication_history.get(
            "current_medications"
        )
        if patient_medications not in (
            None,
            "",
        ):
            medications.append(
                f"Patient-reported: {patient_medications}"
            )

        document_medications = (
            physician_summary.get(
                "medications",
                {},
            )
            or {}
        )

        if isinstance(
            document_medications,
            dict,
        ):
            for medication in document_medications.get(
                "document_derived",
                [],
            ):
                if not isinstance(
                    medication,
                    dict,
                ):
                    continue

                pieces = []
                for key in (
                    "name",
                    "strength",
                    "dose",
                    "frequency",
                    "timing",
                ):
                    value = medication.get(
                        key
                    )
                    if value:
                        pieces.append(
                            str(value)
                        )

                if pieces:
                    medications.append(
                        "Document-derived: "
                        + " ".join(pieces)
                    )

        # --------------------------
        # Allergies
        # --------------------------

        allergies = []

        allergies_value = medication_history.get(
            "allergies"
        )
        if allergies_value not in (
            None,
            "",
        ):
            allergies.append(
                str(allergies_value)
            )

        # --------------------------
        # Relevant documents
        # --------------------------

        relevant_documents = []

        for document in physician_summary.get(
            "documents",
            [],
        ):
            if not isinstance(
                document,
                dict,
            ):
                continue

            value = (
                document.get("document_id")
                or document.get("filename")
                or document.get("document_type")
            )

            if value:
                relevant_documents.append(
                    str(value)
                )

        # --------------------------
        # History string expected by Aurora
        # --------------------------

        hpi_parts = []

        labels = (
            ("onset", "Onset"),
            ("site", "Site"),
            ("character", "Character"),
            ("radiation", "Radiation"),
            (
                "associated_symptoms",
                "Associated symptoms",
            ),
            ("timing", "Timing"),
            (
                "aggravating_factors",
                "Aggravating factors",
            ),
            (
                "relieving_factors",
                "Relieving factors",
            ),
            ("severity", "Severity"),
        )

        for field, label in labels:
            value = hpi.get(
                field
            )
            if value in (
                None,
                "",
            ):
                continue

            hpi_parts.append(
                f"{label}: {value}"
            )

        if not hpi_parts:
            hpi_text = None
        else:
            hpi_text = "; ".join(
                hpi_parts
            )

        return {
            "session_id": session_id,
            "chief_complaint": physician_summary.get(
                "chief_complaint"
            ),
            "history_of_present_illness": hpi_text,
            "past_medical_history": past_medical_history,
            "medications": medications,
            "allergies": allergies,
            "relevant_documents": relevant_documents,
            "clinical_signals": [
                signal["signal_id"]
                for signal in signals
            ],
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }


__all__ = [
    "AuroraClinicalAdapter",
]

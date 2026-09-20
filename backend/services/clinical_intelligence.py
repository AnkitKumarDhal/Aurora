from __future__ import annotations

from typing import Any

from backend.ai.clinical.evidence import EvidenceRecord
from backend.ai.clinical.summary import build_physician_summary
from backend.database.repositories.clinical_signal import ClinicalSignalRepository
from backend.database.repositories.clinical_summary import ClinicalSummaryRepository
from backend.database.repositories.conversation import ConversationRepository
from backend.database.repositories.document import DocumentExtractionRepository, DocumentRepository
from backend.database.repositories.clinical_session import ClinicalSessionRepository
from backend.services.clinical_session import ClinicalSessionService
from backend.services.clinical_signal import ClinicalSignalService
from backend.services.clinical_summary import ClinicalSummaryService
from backend.services.conversation import ConversationService
from backend.services.document import DocumentService


class ClinicalIntelligenceService:
    def __init__(
        self,
        session_service: ClinicalSessionService,
        signal_service: ClinicalSignalService,
        summary_service: ClinicalSummaryService,
        conversation_service: ConversationService,
        document_service: DocumentService,
    ) -> None:
        self.session_service = session_service
        self.signal_service = signal_service
        self.summary_service = summary_service
        self.conversation_service = conversation_service
        self.document_service = document_service

    async def build(
        self,
        session_id: str,
    ) -> dict[str, Any] | None:
        session = await self.session_service.get_session(session_id)

        if session is None:
            return None

        signals = await self.signal_service.get_session_signals(
            session_id,
        )

        summary = await self.summary_service.get_session_summary(
            session_id,
        )

        turns = await self.conversation_service.get_session_turns(
            session_id,
        )

        documents = await self.document_service.get_session_documents(
            session_id,
        )

        document_summaries: list[dict[str, Any]] = []

        for document in documents:
            extraction = await self.document_service.get_extraction(
                document.document_id,
            )

            structured_data = {}

            if extraction is not None and isinstance(
                extraction.structured_data,
                dict,
            ):
                structured_data = extraction.structured_data.get(
                    "structured",
                    extraction.structured_data,
                )

            document_summaries.append(
                {
                    "document_id": document.document_id,
                    "document_type": document.document_type.value.lower(),
                    "filename": document.filename,
                    "date": (
                        structured_data.get("date")
                        if isinstance(structured_data, dict)
                        else None
                    ),
                    "patient_name": (
                        structured_data.get("patient_name")
                        if isinstance(structured_data, dict)
                        else None
                    ),
                    "ocr_confidence": (
                        extraction.structured_data.get("ocr", {}).get(
                            "mean_confidence"
                        )
                        if extraction is not None
                        and isinstance(extraction.structured_data, dict)
                        else None
                    ),
                    "manual_review_required": bool(
                        extraction.structured_data.get(
                            "manual_review_required",
                            False,
                        )
                        if extraction is not None
                        and isinstance(extraction.structured_data, dict)
                        else False
                    ),
                    "review_reasons": list(
                        extraction.structured_data.get(
                            "review_reasons",
                            [],
                        )
                        if extraction is not None
                        and isinstance(extraction.structured_data, dict)
                        else []
                    ),
                    "raw_text": (
                        extraction.extracted_text
                        if extraction is not None
                        else None
                    ),
                    "structured_data": structured_data,
                }
            )

        known_fields = {
            signal.name: signal.value
            for signal in signals
        }

        hpi_fields = {
            field: known_fields[field]
            for field in (
                "onset",
                "site",
                "severity",
                "character",
                "timing",
                "aggravating_factors",
                "relieving_factors",
                "radiation",
                "associated_symptoms",
                "breathing_difficulty",
                "nausea_vomiting",
                "vision_or_neuro",
                "cough",
                "wheeze",
                "location",
                "bowel_changes",
                "appearance",
                "itch_or_pain",
                "spread",
                "urinary_frequency",
                "urinary_burning",
                "urinary_blood",
                "fever",
                "fatigue",
                "weight_change",
            )
            if field in known_fields
        }

        medication_history = {
            "current_medications": (
                summary.medications
                if summary is not None
                else [known_fields["medications"]]
                if "medications" in known_fields
                else []
            ),
            "allergies": (
                summary.allergies
                if summary is not None
                else [known_fields["allergies"]]
                if "allergies" in known_fields
                else []
            ),
        }

        history = {
            "chief_complaint": (
                summary.chief_complaint
                if summary is not None
                else known_fields.get("chief_complaint")
            ),
            "history_of_present_illness": hpi_fields,
            "past_history": {
                "medical_history": known_fields.get(
                    "past_medical_history",
                ),
            },
            "medication_history": medication_history,
        }

        evidence_records: list[dict[str, Any]] = []

        for signal in signals:
            evidence_records.append(
                EvidenceRecord(
                    evidence_id=signal.signal_id,
                    field=signal.name,
                    value=signal.value,
                    source_type="patient_interview",
                    evidence_text=str(signal.value),
                    extraction_method="interview_ai",
                    confidence=signal.confidence,
                    status="reported",
                    metadata={
                        "signal_type": signal.signal_type.value,
                    },
                ).to_dict()
            )

        for document in document_summaries:
            raw_text = str(
                document.get("raw_text") or ""
            ).strip()

            if not raw_text:
                continue

            evidence_records.append(
                EvidenceRecord(
                    evidence_id=str(
                        document["document_id"]
                    ),
                    field="medical_document",
                    value=document.get("document_type"),
                    source_type="medical_document",
                    evidence_text=raw_text,
                    extraction_method="ocr",
                    confidence=document.get(
                        "ocr_confidence"
                    ),
                    status="reported",
                    metadata={
                        "filename": document.get("filename"),
                        "document_type": document.get(
                            "document_type"
                        ),
                    },
                ).to_dict()
            )

        clinical_evidence = {
            "records": evidence_records,
            "count": len(evidence_records),
            "counts_by_source": {
                "patient_interview": sum(
                    record["source_type"] == "patient_interview"
                    for record in evidence_records
                ),
                "medical_document": sum(
                    record["source_type"] == "medical_document"
                    for record in evidence_records
                ),
            },
            "counts_by_status": {
                "reported": len(evidence_records),
            },
        }

        patient_statements = [
            {
                "text": turn.content or "",
                "created_at": turn.created_at.isoformat(),
            }
            for turn in turns
            if turn.content
        ]

        triage = {
            "required": False,
            "red_flags": [
                signal.name
                for signal in signals
                if signal.signal_type.value == "RED_FLAG"
                and signal.value is True
            ],
        }

        intelligence = build_physician_summary(
            clinical_summary={
                "status": (
                    session.status.value
                ),
                "chief_complaint": history.get(
                    "chief_complaint"
                ),
                "clinical_history": history,
                "clinical_evidence": clinical_evidence,
                "triage": triage,
                "patient_statements": patient_statements,
            },
            document_summaries=document_summaries,
            generate_ai_draft=False,
        )

        return {
            "session_id": session_id,
            "session_status": session.status.value,
            "summary": (
                summary.model_dump(mode="json")
                if summary is not None
                else None
            ),
            "documents": document_summaries,
            "intelligence": intelligence,
        }

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from backend.ai.documents.bridge import build_document_summary
from backend.ai.documents.discharge import extract_discharge_summary
from backend.ai.documents.extractor import extract_document
from backend.ai.documents.laboratory import extract_lab_report
from backend.ai.clinical.medication_safety import screen_medication_interactions
from backend.ai.ocr.engine import ocr_document
from backend.database.repositories.document import DocumentExtractionRepository, DocumentRepository
from backend.domain.enums import DocumentStatus, DocumentType


class DocumentProcessingService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        extraction_repository: DocumentExtractionRepository,
    ) -> None:
        self.document_repository = document_repository
        self.extraction_repository = extraction_repository

    async def process_document(self, document_id: str):
        document = await self.document_repository.get_document(document_id)

        if document is None:
            raise ValueError("Document not found")

        extraction = await self.extraction_repository.get_document_extraction(document_id)

        if extraction is None:
            raise ValueError("Document extraction not found")

        await self.document_repository.update_document(
            document_id,
            {"status": DocumentStatus.PROCESSING},
        )

        await self.extraction_repository.update_extraction(
            extraction.extraction_id,
            {
                "status": DocumentStatus.PROCESSING,
                "processed_at": None,
            },
        )

        try:
            if not document.content_type.startswith("image/"):
                raise ValueError(
                    "Only image medical documents are currently supported")

            ocr = await asyncio.to_thread(
                ocr_document,
                document.storage_reference,
            )

            if ocr.get("status") != "success":
                raise ValueError(
                    str(
                        ocr.get(
                            "error",
                            "OCR processing failed",
                        )
                    )
                )

            document_type = str(
                ocr.get("document_type") or "unknown"
            ).strip().lower()

            if document_type == "lab_report":
                structured = await asyncio.to_thread(
                    extract_lab_report,
                    ocr,
                )
            elif document_type == "discharge_summary":
                structured = await asyncio.to_thread(
                    extract_discharge_summary,
                    ocr,
                )
            else:
                structured = await asyncio.to_thread(
                    extract_document,
                    ocr,
                )

            normalized_type = self._document_type(document_type)

            document_record = {
                "document_type": document_type,
                "patient_name": structured.get("patient_name"),
                "date": structured.get("date"),
                "ocr_confidence": ocr.get("mean_confidence"),
                "manual_review_required": bool(
                    ocr.get("manual_review_required")
                    or structured.get("manual_review_required")
                ),
                "review_reasons": list(
                    ocr.get("review_reasons")
                    or structured.get("review_reasons")
                    or []
                ),
                "raw_text": ocr.get("text"),
                "structured_data": structured,
            }

            document_summary = build_document_summary(
                document_record,
            )

            medication_safety = screen_medication_interactions(
                structured.get("medications", [])
            )

            structured_data = {
                "document_type": normalized_type.value,
                "patient_name": structured.get("patient_name"),
                "date": structured.get("date"),
                "ocr": {
                    "status": ocr.get("status"),
                    "mean_confidence": ocr.get("mean_confidence"),
                    "word_count": ocr.get("word_count"),
                    "language": ocr.get("language"),
                    "manual_review_required": bool(
                        ocr.get("manual_review_required")
                    ),
                    "review_reasons": list(
                        ocr.get("review_reasons")
                        or []
                    ),
                },
                "structured": structured,
                "document_summary": document_summary,
                "medication_safety": medication_safety,
            }

            review_reasons = list(
                document_record["review_reasons"]
            )

            if medication_safety.get("requires_physician_review"):
                review_reasons.append(
                    "Supported medication interaction rules require physician or pharmacist review."
                )

            review_required = bool(review_reasons)

            structured_data["manual_review_required"] = review_required
            structured_data["review_reasons"] = review_reasons
            structured_data["raw_text"] = ocr.get("text")

            await self.extraction_repository.update_extraction(
                extraction.extraction_id,
                {
                    "status": DocumentStatus.PROCESSED,
                    "extracted_text": ocr.get("text"),
                    "structured_data": structured_data,
                    "processed_at": datetime.now(timezone.utc),
                },
            )

            return await self.document_repository.update_document(
                document_id,
                {
                    "document_type": normalized_type,
                    "status": DocumentStatus.PROCESSED,
                },
            )

        except Exception as exc:
            error_data: dict[str, Any] = {
                "error": str(exc),
                "processor_status": "failed",
            }

            await self.extraction_repository.update_extraction(
                extraction.extraction_id,
                {
                    "status": DocumentStatus.FAILED,
                    "structured_data": error_data,
                    "processed_at": datetime.now(timezone.utc),
                },
            )

            return await self.document_repository.update_document(
                document_id,
                {"status": DocumentStatus.FAILED},
            )

    @staticmethod
    def _document_type(value: str) -> DocumentType:
        mapping = {
            "prescription": DocumentType.PRESCRIPTION,
            "lab_report": DocumentType.LAB_REPORT,
            "discharge_summary": DocumentType.MEDICAL_RECORD,
            "imaging_report": DocumentType.IMAGING_REPORT,
            "medical_record": DocumentType.MEDICAL_RECORD,
        }

        return mapping.get(
            value,
            DocumentType.OTHER,
        )

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EvidenceRecord:
    evidence_id: str
    field: str
    value: Any
    source_type: str
    evidence_text: str
    extraction_method: str = "direct"
    confidence: Optional[float] = None
    status: str = "reported"
    raw_response_index: Optional[int] = None
    source_field: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "field": self.field,
            "value": deepcopy(self.value),
            "source_type": self.source_type,
            "evidence_text": self.evidence_text,
            "extraction_method": self.extraction_method,
            "confidence": self.confidence,
            "status": self.status,
            "raw_response_index": self.raw_response_index,
            "source_field": self.source_field,
            "metadata": deepcopy(self.metadata),
        }

    # Backward-compatible dictionary-style access.
    # Existing tests and older code can use:
    # record["evidence_id"]
    # record["source_field"]
    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)


class ClinicalEvidenceStore:
    def __init__(self) -> None:
        self._records: List[EvidenceRecord] = []
        self._counter: int = 0

    def _next_id(self, field: str) -> str:
        self._counter += 1

        safe_field = "-".join(
            str(field).strip().split()
        ) or "unknown"

        return f"EVD-{self._counter:04d}-{safe_field}"

    def add(
        self,
        *,
        field: str,
        value: Any,
        source_type: str,
        evidence_text: str,
        extraction_method: str = "direct",
        confidence: Optional[float] = None,
        status: str = "reported",
        raw_response_index: Optional[int] = None,
        source_field: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvidenceRecord:

        record = EvidenceRecord(
            evidence_id=self._next_id(field),
            field=field,
            value=deepcopy(value),
            source_type=source_type,
            evidence_text=str(evidence_text),
            extraction_method=extraction_method,
            confidence=confidence,
            status=status,
            raw_response_index=raw_response_index,
            source_field=source_field,
            metadata=deepcopy(metadata or {}),
        )

        self._records.append(record)

        return record

    def add_patient_fact(
        self,
        *,
        field: str,
        value: Any,
        patient_response: str,
        extraction_method: str = "direct",
        confidence: Optional[float] = None,
        raw_response_index: Optional[int] = None,
        source_field: Optional[str] = None,
        status: str = "reported",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvidenceRecord:

        return self.add(
            field=field,
            value=value,
            source_type="patient_statement",
            evidence_text=patient_response,
            extraction_method=extraction_method,
            confidence=confidence,
            status=status,
            raw_response_index=raw_response_index,
            source_field=source_field,
            metadata=metadata,
        )

    def add_document_fact(
        self,
        *,
        field: str,
        value: Any,
        evidence_text: str,
        extraction_method: str = "document_extraction",
        confidence: Optional[float] = None,
        status: str = "reported",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvidenceRecord:

        return self.add(
            field=field,
            value=value,
            source_type="document",
            evidence_text=evidence_text,
            extraction_method=extraction_method,
            confidence=confidence,
            status=status,
            metadata=metadata,
        )

    def add_contradiction(
        self,
        *,
        field: str,
        previous_value: Any,
        current_value: Any,
        previous_statement: str,
        current_statement: str,
        details: Optional[str] = None,
    ) -> EvidenceRecord:

        evidence_text = (
            f"Previous statement: {previous_statement}\n"
            f"Current statement: {current_statement}"
        )

        metadata = {
            "previous_value": deepcopy(previous_value),
            "current_value": deepcopy(current_value),
        }

        if details:
            metadata["details"] = details

        return self.add(
            field=field,
            value={
                "previous": deepcopy(previous_value),
                "current": deepcopy(current_value),
            },
            source_type="contradiction",
            evidence_text=evidence_text,
            extraction_method="contradiction_detection",
            status="requires_physician_review",
            metadata=metadata,
        )

    def all(self) -> List[EvidenceRecord]:
        return list(self._records)

    def for_field(
        self,
        field: str,
    ) -> List[EvidenceRecord]:

        return [
            record
            for record in self._records
            if record.field == field
        ]

    def counts(self) -> Dict[str, Any]:
        by_source: Dict[str, int] = {}
        by_status: Dict[str, int] = {}

        for record in self._records:
            by_source[record.source_type] = (
                by_source.get(record.source_type, 0) + 1
            )

            by_status[record.status] = (
                by_status.get(record.status, 0) + 1
            )

        return {
            # Newer naming
            "total": len(self._records),
            "by_source_type": by_source,
            "by_status": by_status,

            # Backward-compatible naming
            "count": len(self._records),
            "counts_by_source": by_source,
            "counts_by_status": by_status,
        }

    def to_dict(self) -> Dict[str, Any]:
        by_source: Dict[str, int] = {}
        by_status: Dict[str, int] = {}

        for record in self._records:
            by_source[record.source_type] = (
                by_source.get(record.source_type, 0) + 1
            )

            by_status[record.status] = (
                by_status.get(record.status, 0) + 1
            )

        return {
            "count": len(self._records),
            "records": [
                record.to_dict()
                for record in self._records
            ],
            "counts_by_source": by_source,
            "counts_by_status": by_status,

            # Keep the newer nested structure too.
            "counts": {
                "total": len(self._records),
                "by_source_type": by_source,
                "by_status": by_status,
            },
        }
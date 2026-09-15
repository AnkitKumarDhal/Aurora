from datetime import datetime, timezone

from backend.database.repositories.triage import TriageRepository
from backend.domain.clinical_signal import ClinicalSignal
from backend.domain.enums import TriageStatus, UrgencyLevel
from backend.domain.triage import TriageResult
from backend.models.triage import TriageResultDocument
from backend.services.triage_engine import TriageEngine


class TriageService:
    def __init__(self, repository: TriageRepository, engine: TriageEngine | None = None) -> None:
        self.repository = repository
        self.engine = engine or TriageEngine()

    async def get_result(self, triage_id: str) -> TriageResult | None:
        document = await self.repository.get_result(triage_id)

        if document is None:
            return None

        return self._to_domain(document)

    async def get_session_result(self, session_id: str) -> TriageResult | None:
        document = await self.repository.get_session_result(session_id)

        if document is None:
            return None

        return self._to_domain(document)

    async def create_result(self, result: TriageResult) -> TriageResult:
        document = self._to_document(result)

        await self.repository.create_result(document)

        return result

    async def update_result(self, triage_id: str, updates: dict) -> TriageResult | None:
        document = await self.repository.update_result(triage_id, updates)

        if document is None:
            return None

        return self._to_domain(document)

    async def assess(
        self,
        triage_id: str,
        urgency_level: UrgencyLevel,
        priority_score: int,
        red_flags_present: bool,
    ) -> TriageResult | None:
        return await self.update_result(
            triage_id,
            {
                "status": TriageStatus.ASSESSED,
                "urgency_level": urgency_level,
                "priority_score": priority_score,
                "red_flags_present": red_flags_present,
                "assessed_at": datetime.now(timezone.utc),
            },
        )

    async def assess_from_signals(
        self,
        triage_id: str,
        signals: list[ClinicalSignal]
    ) -> TriageResult | None:
        assessment = self.engine.assess([
            {
                "name": signal.name,
                "value": signal.value,
            }
            for signal in signals
        ])
        return await self.assess(
            triage_id,
            assessment.urgency_level,
            assessment.priority_score,
            assessment.red_flags_present
        )

    async def fail(self, triage_id: str) -> TriageResult | None:
        return await self.update_result(triage_id, {
            "status": TriageStatus.FAILED,
            "assessed_at": datetime.now(timezone.utc),
        },
        )

    @staticmethod
    def _to_domain(document: TriageResultDocument) -> TriageResult:
        return TriageResult(
            triage_id=document.triage_result_id,
            session_id=document.session_id,
            status=document.status,
            urgency_level=document.urgency_level,
            priority_score=document.priority_score,
            red_flags_present=document.red_flags_present,
            assessed_at=document.assessed_at,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @staticmethod
    def _to_document(result: TriageResult) -> TriageResultDocument:
        return TriageResultDocument(
            triage_result_id=result.triage_id,
            session_id=result.session_id,
            status=result.status,
            urgency_level=result.urgency_level,
            priority_score=result.priority_score,
            red_flags_present=result.red_flags_present,
            assessed_at=result.assessed_at,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

from datetime import datetime, timezone

from backend.database.repositories.clinical_summary import ClinicalSummaryRepository
from backend.domain.clinical_summary import ClinicalSummary
from backend.domain.enums import SummaryStatus
from backend.models.clinical_summary import ClinicalSummaryDocument


class ClinicalSummaryService:
    def __init__(self, repository: ClinicalSummaryRepository,) -> None:
        self.repository = repository

    async def get_session_summary(self, session_id: str,) -> ClinicalSummary | None:
        document = await self.repository.get_session_summary(session_id)
        if document is None:
            return None
        return self._to_domain(document)

    async def create_summary(self, summary: ClinicalSummary,) -> ClinicalSummary:
        document = self._to_document(summary)
        await self.repository.create_summary(document)
        return summary

    async def update_summary(self, summary_id: str, updates: dict,) -> ClinicalSummary | None:
        document = await self.repository.update_summary(summary_id, updates,)
        if document is None:
            return None
        return self._to_domain(document)

    async def confirm_summary(self, session_id: str, doctor_id: str,) -> ClinicalSummary | None:
        summary = await self.get_session_summary(session_id)
        if summary is None:
            return None

        summary.status = SummaryStatus.CONFIRMED
        summary.confirmed_by = doctor_id
        summary.confirmed_at = datetime.now(timezone.utc)
        summary.touch()
        document = self._to_document(summary)
        await self.repository.update_summary(summary.summary_id, document.to_mongo(),)
        return summary

    @staticmethod
    def _to_domain(document: ClinicalSummaryDocument,) -> ClinicalSummary:
        return ClinicalSummary(
            summary_id=document.summary_id,
            session_id=document.session_id,
            status=document.status,
            chief_complaint=document.chief_complaint,
            history_of_present_illness=document.history_of_present_illness,
            past_medical_history=document.past_medical_history,
            medications=document.medications,
            allergies=document.allergies,
            relevant_documents=document.relevant_documents,
            clinical_signals=document.clinical_signals,
            generated_at=document.generated_at,
            confirmed_by=document.confirmed_by,
            confirmed_at=document.confirmed_at,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @staticmethod
    def _to_document(summary: ClinicalSummary,) -> ClinicalSummaryDocument:
        return ClinicalSummaryDocument(
            summary_id=summary.summary_id,
            session_id=summary.session_id,
            status=summary.status,
            chief_complaint=summary.chief_complaint,
            history_of_present_illness=summary.history_of_present_illness,
            past_medical_history=summary.past_medical_history,
            medications=summary.medications,
            allergies=summary.allergies,
            relevant_documents=summary.relevant_documents,
            clinical_signals=summary.clinical_signals,
            generated_at=summary.generated_at,
            confirmed_by=summary.confirmed_by,
            confirmed_at=summary.confirmed_at,
            created_at=summary.created_at,
            updated_at=summary.updated_at,
        )

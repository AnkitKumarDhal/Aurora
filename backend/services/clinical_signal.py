from backend.database.repositories.clinical_signal import ClinicalSignalRepository
from backend.domain.clinical_signal import ClinicalSignal
from backend.models.clinical_signal import ClinicalSignalDocument


class ClinicalSignalService:
    def __init__(self, repository: ClinicalSignalRepository,) -> None:
        self.repository = repository

    async def get_signal(self, signal_id: str,) -> ClinicalSignal | None:
        document = await self.repository.get_signal(signal_id)
        if document is None:
            return None
        return self._to_domain(document)

    async def get_session_signals(self, session_id: str,) -> list[ClinicalSignal]:
        documents = await self.repository.get_session_signals(session_id,)
        return [
            self._to_domain(document)
            for document in documents
        ]

    async def create_signal(self, signal: ClinicalSignal,) -> ClinicalSignal:
        document = self._to_document(signal)
        await self.repository.create_signal(document)
        return signal

    async def update_signal(self, signal_id: str, updates: dict,) -> ClinicalSignal | None:
        document = await self.repository.update_signal(signal_id, updates,)
        if document is None:
            return None
        return self._to_domain(document)

    @staticmethod
    def _to_domain(document: ClinicalSignalDocument,) -> ClinicalSignal:
        return ClinicalSignal(
            signal_id=document.signal_id,
            session_id=document.session_id,
            signal_type=document.signal_type,
            name=document.name,
            value=document.value,
            confidence=document.confidence,
            source=document.source,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @staticmethod
    def _to_document(signal: ClinicalSignal,) -> ClinicalSignalDocument:
        return ClinicalSignalDocument(
            signal_id=signal.signal_id,
            session_id=signal.session_id,
            signal_type=signal.signal_type,
            name=signal.name,
            value=signal.value,
            confidence=signal.confidence,
            source=signal.source,
            created_at=signal.created_at,
            updated_at=signal.updated_at,
        )

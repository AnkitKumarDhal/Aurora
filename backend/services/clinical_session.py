from backend.database.repositories.clinical_session import ClinicalSessionRepository
from backend.domain.clinical_session import ClinicalSession
from backend.domain.enums import ConsentStatus, SessionStatus, VerificationStatus
from backend.models.clinical_session import ClinicalSessionDocument


class ClinicalSessionService:
    def __init__(self, repository: ClinicalSessionRepository) -> None:
        self.repository = repository

    async def create_session(self, session: ClinicalSession) -> ClinicalSession:
        document = ClinicalSessionDocument(
            session_id=session.session_id,
            patient_id=session.patient_id,
            department_id=session.department_id,
            status=session.status,
            verification_status=session.verification_status,
            consent_status=session.consent_status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

        await self.repository.create_session(document)
        return session

    async def get_session(self, session_id: str) -> ClinicalSession | None:
        document = await self.repository.get_session(session_id)

        if document is None:
            return None

        return ClinicalSession(
            session_id=document.session_id,
            patient_id=document.patient_id,
            department_id=document.department_id,
            status=document.status,
            verification_status=document.verification_status,
            consent_status=document.consent_status,
            started_at=document.started_at,
            completed_at=document.completed_at,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    async def transition_session(
        self,
        session_id: str,
        new_status: SessionStatus,
    ) -> ClinicalSession | None:
        session = await self.get_session(session_id)

        if session is None:
            return None

        session.transition_to(new_status)

        document = ClinicalSessionDocument(
            session_id=session.session_id,
            patient_id=session.patient_id,
            department_id=session.department_id,
            status=session.status,
            verification_status=session.verification_status,
            consent_status=session.consent_status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

        await self.repository.update_session(
            session_id,
            document.to_mongo(),
        )

        return session

    async def set_identity(
        self,
        session_id: str,
        patient_id: str,
        verification_status: VerificationStatus,
    ) -> ClinicalSession | None:
        session = await self.get_session(session_id)

        if session is None:
            return None

        session.patient_id = patient_id
        session.verification_status = verification_status
        session.touch()

        document = ClinicalSessionDocument(
            session_id=session.session_id,
            patient_id=session.patient_id,
            department_id=session.department_id,
            status=session.status,
            verification_status=session.verification_status,
            consent_status=session.consent_status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

        await self.repository.update_session(
            session_id,
            document.to_mongo(),
        )

        return session

    async def set_consent(
        self,
        session_id: str,
        consent_status: ConsentStatus,
    ) -> ClinicalSession | None:
        session = await self.get_session(session_id)

        if session is None:
            return None

        session.consent_status = consent_status
        session.touch()

        document = ClinicalSessionDocument(
            session_id=session.session_id,
            patient_id=session.patient_id,
            department_id=session.department_id,
            status=session.status,
            verification_status=session.verification_status,
            consent_status=session.consent_status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

        await self.repository.update_session(
            session_id,
            document.to_mongo(),
        )

        return session

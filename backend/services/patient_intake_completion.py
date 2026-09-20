from __future__ import annotations

from hashlib import sha256

from backend.ai.interview.controller import InterviewController
from backend.domain.enums import (
    SessionStatus,
)
from backend.services.clinical_session import ClinicalSessionService
from backend.services.ephemeral_identity import EphemeralIdentityService
from backend.services.workflow import WorkflowService


class PatientIntakeCompletionService:
    def __init__(
        self,
        session_service: ClinicalSessionService,
        ephemeral_identity_service: EphemeralIdentityService,
        interview_controller: InterviewController,
        workflow_service: WorkflowService,
    ) -> None:
        self.session_service = session_service
        self.ephemeral_identity_service = ephemeral_identity_service
        self.interview_controller = interview_controller
        self.workflow_service = workflow_service

    async def complete(
        self,
        session_id: str,
        draft_id: str,
        verification_token: str,
        identity_method: str,
        identity_identifier: str,
    ) -> dict[str, object]:
        await self.ephemeral_identity_service.get_verified_identity(
            draft_id=draft_id,
            token=verification_token,
            method=identity_method,
            identifier=identity_identifier,
        )

        expected_session_id = (
            f"sess_{sha256(draft_id.encode()).hexdigest()[:24]}"
        )

        if session_id != expected_session_id:
            raise ValueError(
                "Draft does not match intake session",
            )

        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status in {
            SessionStatus.HISTORY_IN_PROGRESS,
            SessionStatus.DOCUMENT_PROCESSING,
        }:
            finalized = await self.interview_controller.finalize(
                session_id,
            )

            session = finalized["session"]

        elif session.status not in {
            SessionStatus.SUMMARY_READY,
            SessionStatus.QUEUED,
            SessionStatus.ASSIGNED,
        }:
            raise ValueError(
                "Clinical session is not ready for intake completion",
            )

        queue_entry = await self.workflow_service.queue_and_assign(
            session_id,
        )

        final_session = await self.session_service.get_session(session_id)

        if final_session is None:
            raise ValueError(
                "Clinical session could not be loaded after queueing",
            )

        return {
            "session_id": final_session.session_id,
            "status": final_session.status,
            "queue_entry_id": queue_entry.queue_entry_id,
            "doctor_id": queue_entry.doctor_id,
        }

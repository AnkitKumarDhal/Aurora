from uuid import uuid4

from backend.domain.enums import QueueStatus, SessionStatus
from backend.domain.queue import QueueEntry
from backend.domain.assignment import DoctorAssignment
from backend.services.assignment_scheduler import AssignmentSchedulerService
from backend.services.assignment import AssignmentService
from backend.services.clinical_session import ClinicalSessionService
from backend.services.healthcare_integration import HealthcareIntegrationService
from backend.services.queue import QueueService
from backend.services.triage import TriageService


class WorkflowService:
    def __init__(
        self,
        session_service: ClinicalSessionService,
        queue_service: QueueService,
        assignment_scheduler: AssignmentSchedulerService,
        assignment_service: AssignmentService,
        triage_service: TriageService,
        healthcare_integration_service: HealthcareIntegrationService,
    ) -> None:
        self.session_service = session_service
        self.queue_service = queue_service
        self.assignment_scheduler = assignment_scheduler
        self.assignment_service = assignment_service
        self.triage_service = triage_service
        self.healthcare_integration_service = healthcare_integration_service

    async def queue_session_from_triage(self, session_id: str) -> QueueEntry:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        triage = await self.triage_service.get_session_result(session_id)

        if triage is None:
            raise ValueError("Triage result not found")

        if triage.urgency_level is None:
            raise ValueError("Triage result has no urgency level")

        if triage.priority_score is None:
            raise ValueError("Triage result has no priority score")

        entry = QueueEntry(
            queue_entry_id=f"queue_{uuid4().hex}",
            session_id=session_id,
            department_id=session.department_id,
            urgency_level=triage.urgency_level,
            priority_score=triage.priority_score,
        )

        return await self.queue_session(entry)

    async def queue_session(self, entry: QueueEntry) -> QueueEntry:
        session = await self.session_service.get_session(entry.session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status != SessionStatus.SUMMARY_READY:
            raise ValueError(
                "Session must have a ready summary before queuing",
            )

        if entry.session_id != session.session_id:
            raise ValueError("Queue entry does not belong to session")

        if entry.department_id != session.department_id:
            raise ValueError("Queue entry department does not match session")

        if entry.status != QueueStatus.WAITING:
            raise ValueError("Queue entry must be waiting")

        queued_entry = await self.queue_service.enqueue(entry)

        await self.session_service.transition_session(
            entry.session_id,
            SessionStatus.QUEUED,
        )

        return queued_entry

    async def queue_and_assign(
        self,
        session_id: str,
    ) -> QueueEntry:
        existing_entry = await self.queue_service.get_session_entry(
            session_id,
        )

        if existing_entry is None:
            existing_entry = await self.queue_session_from_triage(
                session_id,
            )

        if (
            existing_entry.status == QueueStatus.WAITING
            and existing_entry.doctor_id is None
        ):
            await self.assign_patient(
                session_id,
                existing_entry.queue_entry_id,
            )

            updated_entry = await self.queue_service.get_entry(
                existing_entry.queue_entry_id,
            )

            if updated_entry is not None:
                existing_entry = updated_entry

        return existing_entry

    async def assign_patient(
        self,
        session_id: str,
        queue_entry_id: str,
    ) -> DoctorAssignment | None:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status != SessionStatus.QUEUED:
            raise ValueError("Session must be queued before assignment")

        entry = await self.queue_service.get_entry(queue_entry_id)

        if entry is None:
            raise ValueError("Queue entry not found")

        if entry.session_id != session_id:
            raise ValueError("Queue entry does not belong to session")

        if entry.department_id != session.department_id:
            raise ValueError("Queue entry department does not match session")

        if entry.status != QueueStatus.WAITING:
            raise ValueError("Queue entry must be waiting before assignment")

        if entry.doctor_id is not None:
            raise ValueError("Queue entry is already assigned")

        assignment = await self.assignment_scheduler.assign(entry)

        if assignment is None:
            return None

        await self.queue_service.update_entry(
            queue_entry_id,
            {"doctor_id": assignment.doctor_id},
        )

        await self.healthcare_integration_service.create_encounter(
            session_id=session_id,
            patient_id=session.patient_id,
            department_id=session.department_id,
        )

        await self.session_service.transition_session(
            session_id,
            SessionStatus.ASSIGNED,
        )

        return assignment

    async def call_patient(
        self,
        session_id: str,
        queue_entry_id: str,
        doctor_id: str | None = None,
    ) -> QueueEntry:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status != SessionStatus.ASSIGNED:
            raise ValueError(
                "Session must be assigned before calling the patient",
            )

        entry = await self.queue_service.get_entry(queue_entry_id)

        if entry is None:
            raise ValueError("Queue entry not found")

        if entry.session_id != session_id:
            raise ValueError("Queue entry does not belong to session")

        if entry.doctor_id is None:
            raise ValueError("Queue entry has no assigned doctor")

        if doctor_id is not None and entry.doctor_id != doctor_id:
            raise ValueError("Doctor is not assigned to this patient")

        if entry.status != QueueStatus.WAITING:
            raise ValueError(
                "Queue entry must be waiting before calling the patient",
            )

        called_entry = await self.queue_service.mark_called(queue_entry_id)

        if called_entry is None:
            raise ValueError("Queue entry could not be called")

        await self.healthcare_integration_service.update_encounter_status(
            f"encounter_{session_id}",
            "arrived",
        )

        await self.session_service.transition_session(
            session_id,
            SessionStatus.CALLED,
        )

        return called_entry

    async def start_consultation(
        self,
        session_id: str,
        queue_entry_id: str,
        doctor_id: str | None = None,
    ) -> QueueEntry:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status != SessionStatus.CALLED:
            raise ValueError("Session must be called before consultation")

        entry = await self.queue_service.get_entry(queue_entry_id)

        if entry is None:
            raise ValueError("Queue entry not found")

        if entry.session_id != session_id:
            raise ValueError("Queue entry does not belong to session")

        if doctor_id is not None and entry.doctor_id != doctor_id:
            raise ValueError("Doctor is not assigned to this patient")

        if entry.status != QueueStatus.CALLED:
            raise ValueError("Queue entry must be called before consultation")

        consultation_entry = await self.queue_service.start_consultation(
            queue_entry_id,
        )

        if consultation_entry is None:
            raise ValueError("Queue entry could not start consultation")

        await self.healthcare_integration_service.update_encounter_status(
            f"encounter_{session_id}",
            "in-progress",
        )

        await self.session_service.transition_session(
            session_id,
            SessionStatus.IN_CONSULTATION,
        )

        return consultation_entry

    async def complete_consultation(
        self,
        session_id: str,
        queue_entry_id: str,
        doctor_id: str | None = None,
    ) -> QueueEntry:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status != SessionStatus.IN_CONSULTATION:
            raise ValueError("Session is not in consultation")

        entry = await self.queue_service.get_entry(queue_entry_id)

        if entry is None:
            raise ValueError("Queue entry not found")

        if entry.session_id != session_id:
            raise ValueError("Queue entry does not belong to session")

        if entry.status != QueueStatus.IN_CONSULTATION:
            raise ValueError("Queue entry is not in consultation")

        assignment = await self.assignment_service.get_session_assignment(
            session_id,
        )

        if assignment is None:
            raise ValueError("Active doctor assignment not found")

        if doctor_id is not None and assignment.doctor_id != doctor_id:
            raise ValueError("Doctor is not assigned to this patient")

        completed_entry = await self.queue_service.complete(queue_entry_id)

        if completed_entry is None:
            raise ValueError("Queue entry could not be completed")

        released_assignment = await self.assignment_service.release_assignment(
            assignment.assignment_id,
        )

        if released_assignment is None:
            raise ValueError("Doctor assignment could not be released")

        await self.healthcare_integration_service.update_encounter_status(
            f"encounter_{session_id}",
            "finished",
        )

        await self.session_service.transition_session(
            session_id,
            SessionStatus.COMPLETED,
        )

        return completed_entry

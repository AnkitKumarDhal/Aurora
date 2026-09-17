from backend.database.repositories.doctor import DoctorRepository
from backend.domain.queue import QueueEntry
from backend.services.clinical_session import ClinicalSessionService
from backend.services.clinical_summary import ClinicalSummaryService
from backend.services.patient import PatientService
from backend.services.queue import QueueService


class DoctorQueueService:
    def __init__(
        self,
        doctor_repository: DoctorRepository,
        session_service: ClinicalSessionService,
        queue_service: QueueService,
        patient_service: PatientService,
        summary_service: ClinicalSummaryService,
    ) -> None:
        self.doctor_repository = doctor_repository
        self.session_service = session_service
        self.queue_service = queue_service
        self.patient_service = patient_service
        self.summary_service = summary_service

    async def get_doctor_queue(
        self,
        doctor_id: str,
    ) -> list[dict[str, object]]:
        doctor = await self.doctor_repository.get_doctor(doctor_id)

        if doctor is None:
            return []

        queue_entries: list[QueueEntry] = []

        for department_id in doctor.department_ids:
            entries = await self.queue_service.get_department_entries(
                department_id,
            )

            queue_entries.extend(
                entry
                for entry in entries
                if entry.doctor_id == doctor_id
            )

        queue_entries.sort(
            key=lambda entry: (
                entry.position
                if entry.position is not None
                else float("inf"),
                entry.queue_entry_id,
            ),
        )

        result: list[dict[str, object]] = []

        for entry in queue_entries:
            session = await self.session_service.get_session(
                entry.session_id,
            )

            if session is None:
                continue

            patient = await self.patient_service.get_patient(
                session.patient_id,
            )

            summary = await self.summary_service.get_session_summary(
                entry.session_id,
            )

            result.append(
                {
                    "queue_entry": entry,
                    "patient": patient,
                    "summary": summary,
                },
            )

        return result

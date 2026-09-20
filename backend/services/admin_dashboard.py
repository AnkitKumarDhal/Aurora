from __future__ import annotations

from datetime import datetime, timezone

from backend.database.repositories.assignment import AssignmentRepository
from backend.database.repositories.doctor import DoctorRepository
from backend.services.clinical_session import ClinicalSessionService
from backend.services.clinical_summary import ClinicalSummaryService
from backend.services.patient import PatientService
from backend.services.queue import QueueService


class AdminDashboardService:
    def __init__(
        self,
        doctor_repository: DoctorRepository,
        assignment_repository: AssignmentRepository,
        queue_service: QueueService,
        session_service: ClinicalSessionService,
        patient_service: PatientService,
        summary_service: ClinicalSummaryService,
    ) -> None:
        self.doctor_repository = doctor_repository
        self.assignment_repository = assignment_repository
        self.queue_service = queue_service
        self.session_service = session_service
        self.patient_service = patient_service
        self.summary_service = summary_service

    async def get_dashboard(
        self,
        department_id: str,
    ) -> dict:
        doctors = await self.doctor_repository.get_department_doctors(
            department_id,
        )

        doctor_map = {
            doctor.doctor_id: doctor
            for doctor in doctors
        }

        doctor_rows = []

        for doctor in doctors:
            assignments = (
                await self.assignment_repository.get_doctor_assignments(
                    doctor.doctor_id,
                )
            )

            doctor_rows.append(
                {
                    "doctor_id": doctor.doctor_id,
                    "display_name": doctor.display_name,
                    "status": (
                        "Available"
                        if doctor.is_available
                        else "Unavailable"
                    ),
                    "assigned_count": len(assignments),
                },
            )

        entries = await self.queue_service.get_department_entries(
            department_id,
        )

        active_entries = [
            entry
            for entry in entries
            if entry.status.value
            not in {
                "COMPLETED",
                "CANCELLED",
            }
        ]

        waiting_entries = [
            entry
            for entry in active_entries
            if entry.status.value
            in {
                "WAITING",
                "CALLED",
                "PROMOTION_PENDING",
            }
        ]

        consultation_entries = [
            entry
            for entry in active_entries
            if entry.status.value == "IN_CONSULTATION"
        ]

        patient_rows = []

        for entry in active_entries:
            session = await self.session_service.get_session(
                entry.session_id,
            )

            if session is None:
                continue

            patient = await self.patient_service.get_patient(
                session.patient_id,
            )

            if patient is None:
                continue

            summary = await self.summary_service.get_session_summary(
                entry.session_id,
            )

            patient_rows.append(
                {
                    "queue_entry_id": entry.queue_entry_id,
                    "session_id": entry.session_id,
                    "patient_id": patient.patient_id,
                    "display_name": patient.display_name,
                    "age": patient.age,
                    "urgency_level": entry.urgency_level,
                    "priority_score": entry.priority_score,
                    "queue_status": entry.status,
                    "doctor_id": entry.doctor_id,
                    "doctor_name": (
                        doctor_map[entry.doctor_id].display_name
                        if entry.doctor_id in doctor_map
                        else None
                    ),
                    "chief_complaint": (
                        summary.chief_complaint
                        if summary is not None
                        else None
                    ),
                    "queued_at": entry.queued_at,
                    "waiting_time_seconds": self._waiting_time_seconds(
                        entry.queued_at,
                        entry.status.value,
                        entry.called_at,
                    ),
                },
            )

        patient_rows.sort(
            key=lambda patient: (
                0
                if patient["queue_status"].value
                == "PROMOTION_PENDING"
                else 1,
                -(
                    patient["priority_score"]
                    if patient["priority_score"] is not None
                    else 0
                ),
                patient["queued_at"]
                or datetime.max.replace(tzinfo=timezone.utc),
            ),
        )

        return {
            "department_id": department_id,
            "stats": {
                "patients": len(active_entries),
                "waiting": len(waiting_entries),
                "in_consultation": len(consultation_entries),
                "doctors": len(doctors),
            },
            "doctors": doctor_rows,
            "patients": patient_rows,
        }

    @staticmethod
    def _waiting_time_seconds(
        queued_at,
        status: str,
        called_at=None,
    ) -> int | None:
        if queued_at is None:
            return None

        queued_time = (
            queued_at.replace(tzinfo=timezone.utc)
            if queued_at.tzinfo is None
            else queued_at.astimezone(timezone.utc)
        )

        if (
            status in {
                "CALLED",
                "IN_CONSULTATION",
                "COMPLETED",
            }
            and called_at is not None
        ):
            end_time = (
                called_at.replace(tzinfo=timezone.utc)
                if called_at.tzinfo is None
                else called_at.astimezone(timezone.utc)
            )
        else:
            end_time = datetime.now(timezone.utc)

        return max(
            0,
            int(
                (end_time - queued_time).total_seconds(),
            ),
        )

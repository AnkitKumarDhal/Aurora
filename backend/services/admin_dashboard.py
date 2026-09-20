from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from backend.database.repositories.assignment import AssignmentRepository
from backend.database.repositories.doctor import DoctorRepository
from backend.services.clinical_session import ClinicalSessionService
from backend.services.clinical_summary import ClinicalSummaryService
from backend.services.patient import PatientService
from backend.services.queue import QueueService


DASHBOARD_TIMEZONE = ZoneInfo(
    "Asia/Kolkata",
)


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
        doctors = (
            await self.doctor_repository.get_department_doctors(
                department_id,
            )
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
                    "assigned_count": len(
                        assignments,
                    ),
                },
            )

        start_at, end_at = self._today_window()

        entries = (
            await self.queue_service.get_department_entries(
                department_id,
                start_at=start_at,
                end_at=end_at,
            )
        )

        waiting_entries = [
            entry
            for entry in entries
            if entry.status.value
            in {
                "WAITING",
                "READY",
                "CALLED",
                "PROMOTION_PENDING",
            }
        ]

        consultation_entries = [
            entry
            for entry in entries
            if entry.status.value
            == "IN_CONSULTATION"
        ]

        patient_rows = []

        for entry in entries:
            session = (
                await self.session_service.get_session(
                    entry.session_id,
                )
            )

            if session is None:
                continue

            patient = (
                await self.patient_service.get_patient(
                    session.patient_id,
                )
            )

            if patient is None:
                continue

            summary = (
                await self.summary_service.get_session_summary(
                    entry.session_id,
                )
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
                        doctor_map[
                            entry.doctor_id
                        ].display_name
                        if entry.doctor_id
                        in doctor_map
                        else None
                    ),
                    "chief_complaint": (
                        summary.chief_complaint
                        if summary is not None
                        else None
                    ),
                    "queued_at": entry.queued_at,
                    "waiting_time_seconds": (
                        self._waiting_time_seconds(
                            entry,
                        )
                    ),
                },
            )

        patient_rows.sort(
            key=self._patient_sort_key,
        )

        return {
            "department_id": department_id,
            "stats": {
                "patients": len(
                    patient_rows,
                ),
                "waiting": len(
                    waiting_entries,
                ),
                "in_consultation": len(
                    consultation_entries,
                ),
                "doctors": len(
                    doctors,
                ),
            },
            "doctors": doctor_rows,
            "patients": patient_rows,
        }

    @staticmethod
    def _today_window() -> tuple[
        datetime,
        datetime,
    ]:
        now_local = datetime.now(
            DASHBOARD_TIMEZONE,
        )

        start_local = now_local.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        end_local = (
            start_local
            + timedelta(days=1)
        )

        return (
            start_local.astimezone(
                timezone.utc,
            ),
            end_local.astimezone(
                timezone.utc,
            ),
        )

    @staticmethod
    def _waiting_time_seconds(
        entry,
    ) -> int | None:
        if entry.queued_at is None:
            return None

        queued_at = (
            entry.queued_at.replace(
                tzinfo=timezone.utc,
            )
            if entry.queued_at.tzinfo is None
            else entry.queued_at.astimezone(
                timezone.utc,
            )
        )

        if (
            entry.status.value
            in {
                "CALLED",
                "IN_CONSULTATION",
            }
            and entry.called_at is not None
        ):
            end_at = (
                entry.called_at.replace(
                    tzinfo=timezone.utc,
                )
                if entry.called_at.tzinfo is None
                else entry.called_at.astimezone(
                    timezone.utc,
                )
            )
        elif (
            entry.status.value
            in {
                "COMPLETED",
                "CANCELLED",
            }
            and entry.completed_at is not None
        ):
            end_at = (
                entry.completed_at.replace(
                    tzinfo=timezone.utc,
                )
                if entry.completed_at.tzinfo is None
                else entry.completed_at.astimezone(
                    timezone.utc,
                )
            )
        else:
            end_at = datetime.now(
                timezone.utc,
            )

        return max(
            0,
            int(
                (
                    end_at
                    - queued_at
                ).total_seconds(),
            ),
        )

    @staticmethod
    def _patient_sort_key(
        patient: dict,
    ) -> tuple:
        status = patient[
            "queue_status"
        ].value

        if status == "PROMOTION_PENDING":
            group = 0
        elif status == "IN_CONSULTATION":
            group = 1
        elif status in {
            "WAITING",
            "READY",
            "CALLED",
        }:
            group = 2
        else:
            group = 3

        return (
            group,
            -(
                patient[
                    "priority_score"
                ]
                if patient[
                    "priority_score"
                ]
                is not None
                else 0
            ),
            -(
                patient[
                    "waiting_time_seconds"
                ]
                if patient[
                    "waiting_time_seconds"
                ]
                is not None
                else 0
            ),
        )

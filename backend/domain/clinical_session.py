from datetime import datetime
from pydantic import Field
from .common import TimestampedModel, utc_now
from .enums import ConsentStatus, SessionStatus, VerificationStatus


class ClinicalSession(TimestampedModel):
    session_id: str = Field(min_length=1)
    patient_id: str = Field(min_length=1)
    department_id: str = Field(min_length=1)
    status: SessionStatus = SessionStatus.CREATED
    verification_status: VerificationStatus = VerificationStatus.PENDING
    consent_status: ConsentStatus = ConsentStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def transition_to(self, new_status: SessionStatus) -> None:
        allowed_transitions: dict[SessionStatus, set[SessionStatus]] = {
            SessionStatus.CREATED: {
                SessionStatus.IDENTIFYING,
                SessionStatus.CANCELLED,
                SessionStatus.ABANDONED,
                SessionStatus.ERROR,
            },
            SessionStatus.IDENTIFYING: {
                SessionStatus.CONSENTED,
                SessionStatus.CANCELLED,
                SessionStatus.ABANDONED,
                SessionStatus.ERROR,
            },
            SessionStatus.CONSENTED: {
                SessionStatus.HISTORY_IN_PROGRESS,
                SessionStatus.CANCELLED,
                SessionStatus.ABANDONED,
                SessionStatus.ERROR,
            },
            SessionStatus.HISTORY_IN_PROGRESS: {
                SessionStatus.DOCUMENT_PROCESSING,
                SessionStatus.SUMMARY_READY,
                SessionStatus.CANCELLED,
                SessionStatus.ABANDONED,
                SessionStatus.ERROR,
            },
            SessionStatus.DOCUMENT_PROCESSING: {
                SessionStatus.SUMMARY_READY,
                SessionStatus.CANCELLED,
                SessionStatus.ABANDONED,
                SessionStatus.ERROR,
            },
            SessionStatus.SUMMARY_READY: {
                SessionStatus.QUEUED,
                SessionStatus.CANCELLED,
                SessionStatus.ERROR,
            },
            SessionStatus.QUEUED: {
                SessionStatus.ASSIGNED,
                SessionStatus.CALLED,
                SessionStatus.CANCELLED,
                SessionStatus.ABANDONED,
                SessionStatus.ERROR,
            },
            SessionStatus.ASSIGNED: {
                SessionStatus.CALLED,
                SessionStatus.QUEUED,
                SessionStatus.CANCELLED,
                SessionStatus.ERROR,
            },
            SessionStatus.CALLED: {
                SessionStatus.IN_CONSULTATION,
                SessionStatus.QUEUED,
                SessionStatus.CANCELLED,
                SessionStatus.ABANDONED,
                SessionStatus.ERROR,
            },
            SessionStatus.IN_CONSULTATION: {
                SessionStatus.COMPLETED,
                SessionStatus.ERROR,
            },
            SessionStatus.COMPLETED: set(),
            SessionStatus.CANCELLED: set(),
            SessionStatus.ABANDONED: set(),
            SessionStatus.ERROR: set(),
        }

        if new_status not in allowed_transitions[self.status]:
            raise ValueError(
                f"Invalid clinical session transition: "
                f"{self.status.value} -> {new_status.value}"
            )

        previous_status = self.status
        self.status = new_status

        if previous_status == SessionStatus.CREATED:
            self.started_at = utc_now()
        if new_status == SessionStatus.COMPLETED:
            self.completed_at = utc_now()

        self.touch()

import asyncio
from datetime import date, datetime, timedelta, timezone

from pwdlib import PasswordHash

from backend.database.connection import (
    close_database,
    get_database_instance,
    initialize_database_connection,
)
from backend.database.initialization import initialize_database
from backend.domain.enums import (
    ActorRole,
    AssignmentStatus,
    ConsentStatus,
    QueueStatus,
    SessionStatus,
    SummaryStatus,
    TriageStatus,
    UrgencyLevel,
    VerificationStatus,
)
from backend.models.assignment import DoctorAssignmentDocument
from backend.models.clinical_session import ClinicalSessionDocument
from backend.models.clinical_summary import ClinicalSummaryDocument
from backend.models.department import DepartmentDocument
from backend.models.doctor import DoctorDocument
from backend.models.patient import PatientDocument
from backend.models.queue import QueueEntryDocument
from backend.models.triage import TriageResultDocument
from backend.models.user import UserDocument


PASSWORD = "Aurora@123"

DEPARTMENT_ID = "general-medicine"

DOCTOR_1_ID = "doctor-demo-1"
DOCTOR_2_ID = "doctor-demo-2"

DOCTOR_1_USER_ID = "user-doctor-demo-1"
DOCTOR_2_USER_ID = "user-doctor-demo-2"
ADMIN_USER_ID = "user-admin-demo"

PATIENT_1_ID = "patient-demo-1"
PATIENT_2_ID = "patient-demo-2"

SESSION_1_ID = "session-demo-1"
SESSION_2_ID = "session-demo-2"

TRIAGE_1_ID = "triage-demo-1"
TRIAGE_2_ID = "triage-demo-2"

QUEUE_1_ID = "queue-demo-1"
QUEUE_2_ID = "queue-demo-2"

ASSIGNMENT_1_ID = "assignment-queue-demo-1"
ASSIGNMENT_2_ID = "assignment-queue-demo-2"

SUMMARY_1_ID = "summary-demo-1"
SUMMARY_2_ID = "summary-demo-2"


def now() -> datetime:
    return datetime.now(timezone.utc)


def build_user(
    user_id: str,
    username: str,
    role: ActorRole,
    actor_id: str,
    password_hash: str,
) -> UserDocument:
    timestamp = now()

    return UserDocument(
        user_id=user_id,
        username=username,
        password_hash=password_hash,
        role=role,
        actor_id=actor_id,
        is_active=True,
        created_at=timestamp,
        updated_at=timestamp,
    )


def mongo_safe(value):
    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(
            value,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

    if isinstance(value, dict):
        return {
            key: mongo_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [mongo_safe(item) for item in value]

    if isinstance(value, tuple):
        return tuple(mongo_safe(item) for item in value)

    return value


async def replace_document(
    collection_name: str,
    identifier: dict,
    document: dict,
) -> None:
    database = get_database_instance()
    await database[collection_name].replace_one(
        identifier,
        mongo_safe(document),
        upsert=True,
    )


async def seed() -> None:
    await initialize_database_connection()
    await initialize_database()

    database = get_database_instance()
    password_hash = PasswordHash.recommended().hash(PASSWORD)

    timestamp = now()

    department = DepartmentDocument(
        department_id=DEPARTMENT_ID,
        name="General Medicine",
        is_active=True,
        created_at=timestamp,
        updated_at=timestamp,
    )

    doctor_1 = DoctorDocument(
        doctor_id=DOCTOR_1_ID,
        display_name="Dr. Aditi Sharma",
        department_ids=[DEPARTMENT_ID],
        is_available=True,
        created_at=timestamp,
        updated_at=timestamp,
    )

    doctor_2 = DoctorDocument(
        doctor_id=DOCTOR_2_ID,
        display_name="Dr. Rahul Das",
        department_ids=[DEPARTMENT_ID],
        is_available=True,
        created_at=timestamp,
        updated_at=timestamp,
    )

    admin_user = build_user(
        ADMIN_USER_ID,
        "admin",
        ActorRole.ADMIN,
        "admin-demo",
        password_hash,
    )

    doctor_1_user = build_user(
        DOCTOR_1_USER_ID,
        "doctor1",
        ActorRole.DOCTOR,
        DOCTOR_1_ID,
        password_hash,
    )

    doctor_2_user = build_user(
        DOCTOR_2_USER_ID,
        "doctor2",
        ActorRole.DOCTOR,
        DOCTOR_2_ID,
        password_hash,
    )

    patient_1 = PatientDocument(
        patient_id=PATIENT_1_ID,
        display_name="Rohan Kumar",
        date_of_birth=date(1998, 4, 18),
        age=28,
        abha_reference="12-3456-7890-1234",
        hospital_reference="AURORA-DEMO-0001",
        created_at=timestamp,
        updated_at=timestamp,
    )

    patient_2 = PatientDocument(
        patient_id=PATIENT_2_ID,
        display_name="Sneha Das",
        date_of_birth=date(1986, 11, 7),
        age=39,
        abha_reference="23-4567-8901-2345",
        hospital_reference="AURORA-DEMO-0002",
        created_at=timestamp,
        updated_at=timestamp,
    )

    session_1 = ClinicalSessionDocument(
        session_id=SESSION_1_ID,
        patient_id=PATIENT_1_ID,
        department_id=DEPARTMENT_ID,
        status=SessionStatus.ASSIGNED,
        verification_status=VerificationStatus.VERIFIED,
        consent_status=ConsentStatus.GRANTED,
        started_at=timestamp - timedelta(minutes=7),
        completed_at=None,
        created_at=timestamp - timedelta(minutes=7),
        updated_at=timestamp,
    )

    session_2 = ClinicalSessionDocument(
        session_id=SESSION_2_ID,
        patient_id=PATIENT_2_ID,
        department_id=DEPARTMENT_ID,
        status=SessionStatus.ASSIGNED,
        verification_status=VerificationStatus.VERIFIED,
        consent_status=ConsentStatus.GRANTED,
        started_at=timestamp - timedelta(minutes=12),
        completed_at=None,
        created_at=timestamp - timedelta(minutes=12),
        updated_at=timestamp,
    )

    summary_1 = ClinicalSummaryDocument(
        summary_id=SUMMARY_1_ID,
        session_id=SESSION_1_ID,
        status=SummaryStatus.READY,
        chief_complaint="Fever and body ache for three days",
        history_of_present_illness="Fever began three days ago with generalized body ache and fatigue. No known breathing difficulty.",
        past_medical_history=["No known chronic illness"],
        medications=[],
        allergies=["No known drug allergies"],
        relevant_documents=[],
        clinical_signals=["FEVER", "BODY_ACHE", "DURATION_3_DAYS"],
        generated_at=timestamp - timedelta(minutes=6),
        confirmed_by=None,
        confirmed_at=None,
        created_at=timestamp - timedelta(minutes=6),
        updated_at=timestamp,
    )

    summary_2 = ClinicalSummaryDocument(
        summary_id=SUMMARY_2_ID,
        session_id=SESSION_2_ID,
        status=SummaryStatus.READY,
        chief_complaint="Persistent cough for two weeks",
        history_of_present_illness="Dry cough for approximately two weeks with intermittent throat irritation. No reported chest pain.",
        past_medical_history=["Asthma"],
        medications=["Salbutamol inhaler as needed"],
        allergies=["Dust"],
        relevant_documents=[],
        clinical_signals=["COUGH", "DURATION_14_DAYS", "HISTORY_ASTHMA"],
        generated_at=timestamp - timedelta(minutes=10),
        confirmed_by=None,
        confirmed_at=None,
        created_at=timestamp - timedelta(minutes=10),
        updated_at=timestamp,
    )

    triage_1 = TriageResultDocument(
        triage_result_id=TRIAGE_1_ID,
        session_id=SESSION_1_ID,
        urgency_level=UrgencyLevel.LEVEL_3,
        priority_score=58,
        red_flags_present=False,
        status=TriageStatus.ASSESSED,
        assessed_at=timestamp - timedelta(minutes=6),
        created_at=timestamp - timedelta(minutes=6),
        updated_at=timestamp,
    )

    triage_2 = TriageResultDocument(
        triage_result_id=TRIAGE_2_ID,
        session_id=SESSION_2_ID,
        urgency_level=UrgencyLevel.LEVEL_2,
        priority_score=34,
        red_flags_present=False,
        status=TriageStatus.ASSESSED,
        assessed_at=timestamp - timedelta(minutes=10),
        created_at=timestamp - timedelta(minutes=10),
        updated_at=timestamp,
    )

    queue_1 = QueueEntryDocument(
        queue_entry_id=QUEUE_1_ID,
        session_id=SESSION_1_ID,
        department_id=DEPARTMENT_ID,
        status=QueueStatus.WAITING,
        position=1,
        urgency_level=UrgencyLevel.LEVEL_3,
        priority_score=58,
        doctor_id=DOCTOR_1_ID,
        queued_at=timestamp - timedelta(minutes=6),
        called_at=None,
        completed_at=None,
        created_at=timestamp - timedelta(minutes=6),
        updated_at=timestamp,
    )

    queue_2 = QueueEntryDocument(
        queue_entry_id=QUEUE_2_ID,
        session_id=SESSION_2_ID,
        department_id=DEPARTMENT_ID,
        status=QueueStatus.WAITING,
        position=2,
        urgency_level=UrgencyLevel.LEVEL_2,
        priority_score=34,
        doctor_id=DOCTOR_2_ID,
        queued_at=timestamp - timedelta(minutes=4),
        called_at=None,
        completed_at=None,
        created_at=timestamp - timedelta(minutes=4),
        updated_at=timestamp,
    )

    assignment_1 = DoctorAssignmentDocument(
        assignment_id=ASSIGNMENT_1_ID,
        session_id=SESSION_1_ID,
        doctor_id=DOCTOR_1_ID,
        department_id=DEPARTMENT_ID,
        status=AssignmentStatus.ACTIVE,
        assigned_at=timestamp - timedelta(minutes=5),
        released_at=None,
        created_at=timestamp - timedelta(minutes=5),
        updated_at=timestamp,
    )

    assignment_2 = DoctorAssignmentDocument(
        assignment_id=ASSIGNMENT_2_ID,
        session_id=SESSION_2_ID,
        doctor_id=DOCTOR_2_ID,
        department_id=DEPARTMENT_ID,
        status=AssignmentStatus.ACTIVE,
        assigned_at=timestamp - timedelta(minutes=3),
        released_at=None,
        created_at=timestamp - timedelta(minutes=3),
        updated_at=timestamp,
    )

    seed_documents = (
        ("departments", "department_id", department),
        ("doctors", "doctor_id", doctor_1),
        ("doctors", "doctor_id", doctor_2),
        ("users", "user_id", admin_user),
        ("users", "user_id", doctor_1_user),
        ("users", "user_id", doctor_2_user),
        ("patients", "patient_id", patient_1),
        ("patients", "patient_id", patient_2),
        ("clinical_sessions", "session_id", session_1),
        ("clinical_sessions", "session_id", session_2),
        ("clinical_summaries", "summary_id", summary_1),
        ("clinical_summaries", "summary_id", summary_2),
        ("triage_results", "triage_result_id", triage_1),
        ("triage_results", "triage_result_id", triage_2),
        ("queue_entries", "queue_entry_id", queue_1),
        ("queue_entries", "queue_entry_id", queue_2),
        ("doctor_assignments", "assignment_id", assignment_1),
        ("doctor_assignments", "assignment_id", assignment_2),
    )

    for collection_name, field_name, model in seed_documents:
        await replace_document(
            collection_name,
            {field_name: getattr(model, field_name)},
            model.model_dump(exclude_none=True),
        )

    await database.documents.delete_many(
        {"session_id": {"$in": [SESSION_1_ID, SESSION_2_ID]}},
    )
    await database.conversation_turns.delete_many(
        {"session_id": {"$in": [SESSION_1_ID, SESSION_2_ID]}},
    )
    await database.clinical_signals.delete_many(
        {"session_id": {"$in": [SESSION_1_ID, SESSION_2_ID]}},
    )
    await database.document_extractions.delete_many(
        {"document_id": {"$in": []}},
    )
    await database.promotion_requests.delete_many(
        {"queue_entry_id": {"$in": [QUEUE_1_ID, QUEUE_2_ID]}},
    )

    print("Aurora demo data seeded.")
    print("Admin: admin / Aurora@123")
    print("Doctor 1: doctor1 / Aurora@123")
    print("Doctor 2: doctor2 / Aurora@123")


async def main() -> None:
    try:
        await seed()
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())

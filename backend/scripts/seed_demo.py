import asyncio
from datetime import date, datetime, timedelta, timezone
from pwdlib import PasswordHash
from backend.database.connection import close_database, get_database_instance, initialize_database_connection
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

OLD_PATIENT_IDS = (
    "patient-demo-1",
    "patient-demo-2",
)

OLD_SESSION_IDS = (
    "session-demo-1",
    "session-demo-2",
)

DEMO_CASES = (
    {
        "patient_id": "patient-queue-1",
        "session_id": "session-queue-1",
        "triage_id": "triage-queue-1",
        "queue_id": "queue-queue-1",
        "assignment_id": "assignment-queue-1",
        "summary_id": "summary-queue-1",
        "display_name": "S. Patnaik",
        "date_of_birth": date(1989, 2, 14),
        "age": 37,
        "abha_reference": "11-2233-4455-6677",
        "hospital_reference": "AURORA-DEMO-001",
        "session_status": SessionStatus.ASSIGNED,
        "queue_status": QueueStatus.WAITING,
        "urgency_level": UrgencyLevel.LEVEL_5,
        "priority_score": 100,
        "red_flags_present": True,
        "queued_minutes": 3,
        "called_minutes": None,
        "summary_status": SummaryStatus.READY,
        "confirmed_by": None,
        "confirmed_minutes": None,
        "chief_complaint": "Severe chest pain radiating to left arm",
        "history_of_present_illness": "Sudden onset of severe chest pain with sweating and breathlessness.",
        "past_medical_history": ["Hypertension"],
        "medications": ["Amlodipine 5mg OD"],
        "allergies": [],
    },
    {
        "patient_id": "patient-queue-2",
        "session_id": "session-queue-2",
        "triage_id": "triage-queue-2",
        "queue_id": "queue-queue-2",
        "assignment_id": "assignment-queue-2",
        "summary_id": "summary-queue-2",
        "display_name": "A. Kumar",
        "date_of_birth": date(2005, 8, 21),
        "age": 21,
        "abha_reference": "22-3344-5566-7788",
        "hospital_reference": "AURORA-DEMO-002",
        "session_status": SessionStatus.ASSIGNED,
        "queue_status": QueueStatus.WAITING,
        "urgency_level": UrgencyLevel.LEVEL_4,
        "priority_score": 80,
        "red_flags_present": False,
        "queued_minutes": 12,
        "called_minutes": None,
        "summary_status": SummaryStatus.READY,
        "confirmed_by": None,
        "confirmed_minutes": None,
        "chief_complaint": "Fever and cough for three days",
        "history_of_present_illness": "Fever with cough and fatigue for approximately three days.",
        "past_medical_history": [],
        "medications": [],
        "allergies": [],
    },
    {
        "patient_id": "patient-queue-3",
        "session_id": "session-queue-3",
        "triage_id": "triage-queue-3",
        "queue_id": "queue-queue-3",
        "assignment_id": "assignment-queue-3",
        "summary_id": "summary-queue-3",
        "display_name": "T. Behera",
        "date_of_birth": date(1979, 6, 9),
        "age": 47,
        "abha_reference": "33-4455-6677-8899",
        "hospital_reference": "AURORA-DEMO-003",
        "session_status": SessionStatus.ASSIGNED,
        "queue_status": QueueStatus.PROMOTION_PENDING,
        "urgency_level": UrgencyLevel.LEVEL_3,
        "priority_score": 62,
        "red_flags_present": False,
        "queued_minutes": 18,
        "called_minutes": None,
        "summary_status": SummaryStatus.READY,
        "confirmed_by": None,
        "confirmed_minutes": None,
        "chief_complaint": "Persistent abdominal discomfort, moderate",
        "history_of_present_illness": "Persistent abdominal discomfort with reduced appetite over the past several days.",
        "past_medical_history": [],
        "medications": [],
        "allergies": [],
    },
    {
        "patient_id": "patient-queue-4",
        "session_id": "session-queue-4",
        "triage_id": "triage-queue-4",
        "queue_id": "queue-queue-4",
        "assignment_id": "assignment-queue-4",
        "summary_id": "summary-queue-4",
        "display_name": "M. Nayak",
        "date_of_birth": date(1996, 1, 25),
        "age": 29,
        "abha_reference": "44-5566-7788-9900",
        "hospital_reference": "AURORA-DEMO-004",
        "session_status": SessionStatus.ASSIGNED,
        "queue_status": QueueStatus.WAITING,
        "urgency_level": UrgencyLevel.LEVEL_1,
        "priority_score": 20,
        "red_flags_present": False,
        "queued_minutes": 26,
        "called_minutes": None,
        "summary_status": SummaryStatus.READY,
        "confirmed_by": None,
        "confirmed_minutes": None,
        "chief_complaint": "Mild headache and nasal congestion",
        "history_of_present_illness": "Mild intermittent headache with nasal congestion and no reported fever.",
        "past_medical_history": [],
        "medications": [],
        "allergies": [],
    },
    {
        "patient_id": "patient-queue-5",
        "session_id": "session-queue-5",
        "triage_id": "triage-queue-5",
        "queue_id": "queue-queue-5",
        "assignment_id": "assignment-queue-5",
        "summary_id": "summary-queue-5",
        "display_name": "P. Sethi",
        "date_of_birth": date(1993, 5, 17),
        "age": 33,
        "abha_reference": "55-6677-8899-0011",
        "hospital_reference": "AURORA-DEMO-005",
        "session_status": SessionStatus.CALLED,
        "queue_status": QueueStatus.CALLED,
        "urgency_level": UrgencyLevel.LEVEL_3,
        "priority_score": 55,
        "red_flags_present": False,
        "queued_minutes": 31,
        "called_minutes": 7,
        "summary_status": SummaryStatus.READY,
        "confirmed_by": None,
        "confirmed_minutes": None,
        "chief_complaint": "Lower back pain, moderate, three weeks",
        "history_of_present_illness": "Lower back pain for approximately three weeks with intermittent stiffness.",
        "past_medical_history": [],
        "medications": [],
        "allergies": [],
    },
    {
        "patient_id": "patient-queue-6",
        "session_id": "session-queue-6",
        "triage_id": "triage-queue-6",
        "queue_id": "queue-queue-6",
        "assignment_id": "assignment-queue-6",
        "summary_id": "summary-queue-6",
        "display_name": "G. Rout",
        "date_of_birth": date(1965, 10, 3),
        "age": 61,
        "abha_reference": "66-7788-9900-1122",
        "hospital_reference": "AURORA-DEMO-006",
        "session_status": SessionStatus.IN_CONSULTATION,
        "queue_status": QueueStatus.IN_CONSULTATION,
        "urgency_level": UrgencyLevel.LEVEL_2,
        "priority_score": 30,
        "red_flags_present": False,
        "queued_minutes": 45,
        "called_minutes": 40,
        "summary_status": SummaryStatus.CONFIRMED,
        "confirmed_by": DOCTOR_1_ID,
        "confirmed_minutes": 2,
        "chief_complaint": "Follow-up: hypertension review",
        "history_of_present_illness": "Routine hypertension follow-up with review of home blood pressure readings.",
        "past_medical_history": ["Hypertension"],
        "medications": ["Amlodipine 5mg OD"],
        "allergies": [],
    },
)


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


def build_case_documents(
    case: dict,
    timestamp: datetime,
) -> tuple[tuple[str, str, object], ...]:
    queued_at = timestamp - timedelta(
        minutes=case["queued_minutes"],
    )

    called_at = None

    if case["called_minutes"] is not None:
        called_at = timestamp - timedelta(
            minutes=case["called_minutes"],
        )

    confirmed_at = None

    if case["confirmed_minutes"] is not None:
        confirmed_at = timestamp - timedelta(
            minutes=case["confirmed_minutes"],
        )

    patient = PatientDocument(
        patient_id=case["patient_id"],
        display_name=case["display_name"],
        date_of_birth=case["date_of_birth"],
        age=case["age"],
        abha_reference=case["abha_reference"],
        hospital_reference=case["hospital_reference"],
        created_at=timestamp - timedelta(
            minutes=case["queued_minutes"],
        ),
        updated_at=timestamp,
    )

    session = ClinicalSessionDocument(
        session_id=case["session_id"],
        patient_id=case["patient_id"],
        department_id=DEPARTMENT_ID,
        status=case["session_status"],
        verification_status=VerificationStatus.VERIFIED,
        consent_status=ConsentStatus.GRANTED,
        started_at=(
            timestamp - timedelta(
                minutes=max(
                    case["queued_minutes"] - 1,
                    1,
                ),
            )
        ),
        completed_at=None,
        created_at=queued_at,
        updated_at=timestamp,
    )

    summary = ClinicalSummaryDocument(
        summary_id=case["summary_id"],
        session_id=case["session_id"],
        status=case["summary_status"],
        chief_complaint=case["chief_complaint"],
        history_of_present_illness=case["history_of_present_illness"],
        past_medical_history=case["past_medical_history"],
        medications=case["medications"],
        allergies=case["allergies"],
        relevant_documents=[],
        clinical_signals=[],
        generated_at=queued_at,
        confirmed_by=case["confirmed_by"],
        confirmed_at=confirmed_at,
        created_at=queued_at,
        updated_at=timestamp,
    )

    triage = TriageResultDocument(
        triage_result_id=case["triage_id"],
        session_id=case["session_id"],
        urgency_level=case["urgency_level"],
        priority_score=case["priority_score"],
        red_flags_present=case["red_flags_present"],
        status=TriageStatus.ASSESSED,
        assessed_at=queued_at,
        created_at=queued_at,
        updated_at=timestamp,
    )

    queue_entry = QueueEntryDocument(
        queue_entry_id=case["queue_id"],
        session_id=case["session_id"],
        department_id=DEPARTMENT_ID,
        status=case["queue_status"],
        position=case["position"],
        urgency_level=case["urgency_level"],
        priority_score=case["priority_score"],
        doctor_id=DOCTOR_1_ID,
        queued_at=queued_at,
        called_at=called_at,
        completed_at=None,
        created_at=queued_at,
        updated_at=timestamp,
    )

    assignment = DoctorAssignmentDocument(
        assignment_id=case["assignment_id"],
        session_id=case["session_id"],
        doctor_id=DOCTOR_1_ID,
        department_id=DEPARTMENT_ID,
        status=AssignmentStatus.ACTIVE,
        assigned_at=queued_at,
        released_at=None,
        created_at=queued_at,
        updated_at=timestamp,
    )

    return (
        ("patients", "patient_id", patient),
        ("clinical_sessions", "session_id", session),
        ("clinical_summaries", "summary_id", summary),
        ("triage_results", "triage_result_id", triage),
        ("queue_entries", "queue_entry_id", queue_entry),
        ("doctor_assignments", "assignment_id", assignment),
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

    seed_documents = [
        (
            "departments",
            "department_id",
            department,
        ),
        (
            "doctors",
            "doctor_id",
            doctor_1,
        ),
        (
            "doctors",
            "doctor_id",
            doctor_2,
        ),
        (
            "users",
            "user_id",
            admin_user,
        ),
        (
            "users",
            "user_id",
            doctor_1_user,
        ),
        (
            "users",
            "user_id",
            doctor_2_user,
        ),
    ]

    for case in DEMO_CASES:
        case_data = dict(case)
        case_data["position"] = len(
            seed_documents,
        )

    case_documents = []

    for index, case in enumerate(DEMO_CASES, start=1):
        case_data = dict(case)
        case_data["position"] = index

        case_documents.extend(
            build_case_documents(
                case_data,
                timestamp,
            ),
        )

    seed_documents.extend(case_documents)

    cleanup_session_ids = list(OLD_SESSION_IDS)
    cleanup_session_ids.extend(
        case["session_id"]
        for case in DEMO_CASES
    )

    cleanup_patient_ids = list(OLD_PATIENT_IDS)
    cleanup_patient_ids.extend(
        case["patient_id"]
        for case in DEMO_CASES
    )

    cleanup_queue_ids = [
        case["queue_id"]
        for case in DEMO_CASES
    ]

    document_cursor = database.documents.find(
        {
            "session_id": {
                "$in": cleanup_session_ids,
            },
        },
        {
            "document_id": 1,
        },
    )

    document_ids = [
        document["document_id"]
        async for document in document_cursor
    ]

    if document_ids:
        await database.document_extractions.delete_many({"document_id": {"$in": document_ids, }})

    await database.documents.delete_many({"session_id": {"$in": cleanup_session_ids}})
    await database.conversation_turns.delete_many({"session_id": {"$in": cleanup_session_ids}})
    await database.clinical_signals.delete_many({"session_id": {"$in": cleanup_session_ids}})
    await database.promotion_requests.delete_many({"queue_entry_id": {"$in": cleanup_queue_ids}})
    await database.queue_entries.delete_many({"queue_entry_id": {"$in": cleanup_queue_ids}})
    await database.doctor_assignments.delete_many({"session_id": {"$in": cleanup_session_ids}})
    await database.triage_results.delete_many({"session_id": {"$in": cleanup_session_ids}})
    await database.clinical_summaries.delete_many({"session_id": {"$in": cleanup_session_ids}})
    await database.clinical_sessions.delete_many({"session_id": {"$in": cleanup_session_ids}})
    await database.patients.delete_many({"patient_id": {"$in": cleanup_patient_ids}})

    for collection_name, field_name, model in seed_documents:
        await replace_document(
            collection_name,
            {
                field_name: getattr(
                    model,
                    field_name,
                ),
            },
            model.model_dump(
                exclude_none=True,
            ),
        )

    print("Aurora demo data seeded.")
    print("Doctor 1: doctor1 / Aurora@123")
    print("Doctor 2: doctor2 / Aurora@123")
    print("Admin: admin / Aurora@123")


async def main() -> None:
    try:
        await seed()
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())

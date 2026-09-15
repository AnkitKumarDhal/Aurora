from enum import Enum


class ActorRole(str, Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"


class AssignmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    RELEASED = "RELEASED"


class ClinicalSignalType(str, Enum):
    ALLERGY = "ALLERGY"
    DURATION = "DURATION"
    HISTORY = "HISTORY"
    MEDICATION = "MEDICATION"
    OTHER = "OTHER"
    RED_FLAG = "RED_FLAG"
    SYMPTOM = "SYMPTOM"
    VITAL = "VITAL"


class ConsentStatus(str, Enum):
    DENIED = "DENIED"
    GRANTED = "GRANTED"
    PENDING = "PENDING"


class ConversationInputType(str, Enum):
    AUDIO = "AUDIO"
    GUIDED_INPUT = "GUIDED_INPUT"
    TEXT = "TEXT"


class DocumentStatus(str, Enum):
    FAILED = "FAILED"
    PROCESSED = "PROCESSED"
    PROCESSING = "PROCESSING"
    UPLOADED = "UPLOADED"


class DocumentType(str, Enum):
    IMAGING_REPORT = "IMAGING_REPORT"
    LAB_REPORT = "LAB_REPORT"
    MEDICAL_RECORD = "MEDICAL_RECORD"
    OTHER = "OTHER"
    PRESCRIPTION = "PRESCRIPTION"


class PromotionStatus(str, Enum):
    APPROVED = "APPROVED"
    AUTO_APPROVED = "AUTO_APPROVED"
    CANCELLED = "CANCELLED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"


class QueueStatus(str, Enum):
    CALLED = "CALLED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    IN_CONSULTATION = "IN_CONSULTATION"
    PROMOTION_PENDING = "PROMOTION_PENDING"
    READY = "READY"
    WAITING = "WAITING"


class SessionStatus(str, Enum):
    ABANDONED = "ABANDONED"
    ASSIGNED = "ASSIGNED"
    CALLED = "CALLED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    CONSENTED = "CONSENTED"
    CREATED = "CREATED"
    DOCUMENT_PROCESSING = "DOCUMENT_PROCESSING"
    ERROR = "ERROR"
    HISTORY_IN_PROGRESS = "HISTORY_IN_PROGRESS"
    IDENTIFYING = "IDENTIFYING"
    IN_CONSULTATION = "IN_CONSULTATION"
    QUEUED = "QUEUED"
    SUMMARY_READY = "SUMMARY_READY"


class Speaker(str, Enum):
    PATIENT = "PATIENT"
    SYSTEM = "SYSTEM"


class SummaryStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    GENERATING = "GENERATING"
    READY = "READY"


class TriageStatus(str, Enum):
    ASSESSED = "ASSESSED"
    FAILED = "FAILED"
    PENDING = "PENDING"


class UrgencyLevel(int, Enum):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5


class VerificationStatus(str, Enum):
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"

from .assignment import DoctorAssignmentDocument
from .clinical_session import ClinicalSessionDocument
from .clinical_signal import ClinicalSignalDocument
from .clinical_summary import ClinicalSummaryDocument
from .conversation import ConversationTurnDocument
from .department import DepartmentDocument
from .document import DocumentDocument, DocumentExtractionDocument
from .doctor import DoctorDocument
from .patient import PatientDocument
from .promotion import PromotionRequestDocument
from .queue import QueueEntryDocument
from .triage import TriageResultDocument

__all__ = [
    "PatientDocument",
    "DoctorDocument",
    "DepartmentDocument",
    "ClinicalSessionDocument",
    "ConversationTurnDocument",
    "ClinicalSignalDocument",
    "DocumentDocument",
    "DocumentExtractionDocument",
    "ClinicalSummaryDocument",
    "TriageResultDocument",
    "QueueEntryDocument",
    "DoctorAssignmentDocument",
    "PromotionRequestDocument",
]

export type ActorRole = "DOCTOR" | "ADMIN";

export type QueueStatus =
  | "WAITING"
  | "PROMOTION_PENDING"
  | "CALLED"
  | "IN_CONSULTATION"
  | "COMPLETED"
  | "CANCELLED";

export type UrgencyLevel = 1 | 2 | 3 | 4 | 5;

export type SessionStatus =
  | "CREATED"
  | "IDENTIFYING"
  | "CONSENTED"
  | "HISTORY_IN_PROGRESS"
  | "DOCUMENT_PROCESSING"
  | "SUMMARY_READY"
  | "QUEUED"
  | "ASSIGNED"
  | "CALLED"
  | "IN_CONSULTATION"
  | "COMPLETED"
  | "CANCELLED"
  | "ABANDONED"
  | "ERROR";

export type VerificationStatus = string;
export type ConsentStatus = string;
export type AssignmentStatus = string;
export type TriageStatus = string;
export type DocumentStatus = "UPLOADED" | "PROCESSING" | "PROCESSED" | "FAILED";
export type DocumentType = string;

export interface DocumentExtraction {
  extraction_id: string;
  document_id: string;
  status: DocumentStatus;
  extracted_text: string | null;
  structured_data: Record<string, unknown> | null;
  processed_at: string | null;
  created_at: string;
  updated_at: string;
}
export type SummaryStatus = string;

export interface ApiError {
  detail: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface CurrentUser {
  user_id: string;
  username: string;
  display_name: string | null;
  role: ActorRole;
  actor_id: string;
}

export interface DoctorQueuePatient {
  patient_id: string;
  display_name: string;
  age: number | null;
}

export interface ClinicalSummary {
  summary_id: string;
  session_id: string;
  status: SummaryStatus;
  chief_complaint: string | null;
  history_of_present_illness: string | null;
  past_medical_history: string[];
  medications: string[];
  allergies: string[];
  relevant_documents: string[];
  clinical_signals: string[];
  generated_at: string | null;
  confirmed_by: string | null;
  confirmed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DoctorQueueEntry {
  queue_entry_id: string;
  session_id: string;
  position: number | null;
  urgency_level: UrgencyLevel | null;
  waiting_time_seconds: number | null;
  doctor_id: string | null;
  status: QueueStatus;
  patient: DoctorQueuePatient | null;
  summary: ClinicalSummary | null;
  queued_at: string | null;
  called_at: string | null;
}

export interface DoctorQueueResponse {
  entries: DoctorQueueEntry[];
}

export interface DoctorCasePatient {
  patient_id: string;
  display_name: string;
  date_of_birth: string | null;
  age: number | null;
  abha_reference: string | null;
  hospital_reference: string | null;
}

export interface DoctorCaseSession {
  session_id: string;
  patient_id: string;
  department_id: string;
  status: SessionStatus;
  verification_status: VerificationStatus;
  consent_status: ConsentStatus;
  created_at: string;
  updated_at: string;
}

export interface DoctorCaseDocument {
  document_id: string;
  session_id: string;
  filename: string;
  document_type: DocumentType;
  content_type: string;
  size_bytes: number;
  storage_reference: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
}

export interface DoctorCaseTriage {
  triage_id: string;
  session_id: string;
  status: TriageStatus;
  urgency_level: UrgencyLevel | null;
  priority_score: number | null;
  red_flags_present: boolean;
  assessed_at: string | null;
}

export interface DoctorCaseAssignment {
  assignment_id: string;
  session_id: string;
  doctor_id: string;
  department_id: string;
  status: AssignmentStatus;
  assigned_at: string | null;
  released_at: string | null;
}

export interface DoctorCaseResponse {
  session: DoctorCaseSession;
  patient: DoctorCasePatient | null;
  summary: ClinicalSummary | null;
  documents: DoctorCaseDocument[];
  triage: DoctorCaseTriage | null;
  assignment: DoctorCaseAssignment | null;
}

export interface QueueActionResponse {
  queue_entry: {
    queue_entry_id: string;
    session_id: string;
    department_id: string;
    status: QueueStatus;
    position: number | null;
    urgency_level: UrgencyLevel | null;
    priority_score: number | null;
    doctor_id: string | null;
    queued_at: string | null;
    called_at: string | null;
    completed_at: string | null;
  };
}

export interface ConversationTurn {
  turn_id: string;
  session_id: string;
  speaker: string;
  input_type: "AUDIO" | "GUIDED_INPUT" | "TEXT";
  content: string | null;
  language: string | null;
  media_reference: string | null;
  created_at: string;
}

export interface ConversationHistoryResponse {
  turns: ConversationTurn[];
}

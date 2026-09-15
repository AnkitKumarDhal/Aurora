# Aurora API Contract

This document defines the HTTP API contract between Aurora's frontend applications and backend services.

The contract describes:

- Patient intake and verification
- Consent
- Clinical intake sessions
- Conversation turns
- Document uploads and processing
- Clinical summaries
- Triage and priority
- Department-wide patient queue
- Doctor assignment
- Doctor case review
- Promotion requests
- Admin/reception operations
- Mock ABHA/FHIR/HIS integrations

AI implementation details, model providers, OCR engines, speech services, and external healthcare-system implementations are intentionally kept behind backend boundaries.

---

## 1. API Conventions

### Base URL

Development:

```text
http://localhost:8000/api/v1
```

Production deployment may use a different base URL.

All application endpoints are versioned under `/api/v1`.

---

## 2. Authentication and Authorization

Aurora has three application roles:

```text
PATIENT
DOCTOR
ADMIN
```

The patient kiosk does not use a conventional Aurora username/password login.

Instead, the patient goes through a verification flow associated with the current clinical session.

Doctors and administrators use authenticated application sessions.

### Authorization rules

| Resource / Action | Patient | Doctor | Admin |
|---|---:|---:|---:|
| Start intake session | Yes | No | No |
| Verify patient identity | Yes | No | No |
| Provide consent | Yes | No | No |
| Submit conversation data | Yes | No | No |
| Upload documents | Yes | No | No |
| View own intake progress | Yes | No | No |
| View assigned patient case | No | Yes | Yes |
| Review/edit clinical summary | No | Yes | No |
| View department queue | No | Yes | Yes |
| Change clinical priority | No | No | No |
| Assign doctor | No | No | Yes/system |
| Approve/deny promotion | No | No | Yes |
| Manage operational queue | No | No | Yes |

Authorization is enforced by the backend.

Frontend visibility is not considered an authorization mechanism.

---

# 3. Common Response Format

Successful responses should return JSON.

A successful single-resource response follows this general structure:

```json
{
  "data": {},
  "meta": {}
}
```

`meta` is optional.

Collection responses use:

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

Pagination may be replaced by cursor-based pagination if required later.

---

# 4. Error Format

All API errors should use a consistent structure:

```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "The requested clinical session does not exist.",
    "details": {}
  }
}
```

### Standard HTTP status codes

| Status | Meaning |
|---|---|
| `200` | Successful request |
| `201` | Resource created |
| `202` | Request accepted for asynchronous processing |
| `204` | Successful request with no response body |
| `400` | Invalid request |
| `401` | Authentication required/invalid |
| `403` | Authenticated but not authorized |
| `404` | Resource not found |
| `409` | Resource/state conflict |
| `422` | Validation failure |
| `429` | Rate limit exceeded |
| `500` | Internal server error |
| `503` | Required service temporarily unavailable |

---

# 5. Patient Intake Session

A `ClinicalSession` represents one OPD intake interaction.

It is the central object connecting:

- Patient verification
- Consent
- Conversation
- Documents
- Clinical summary
- Triage
- Queue entry
- Doctor assignment
- Consultation

## Session lifecycle

```text
CREATED
   ↓
IDENTIFYING
   ↓
CONSENTED
   ↓
HISTORY_IN_PROGRESS
   ↓
DOCUMENT_PROCESSING
   ↓
SUMMARY_READY
   ↓
QUEUED
   ↓
ASSIGNED
   ↓
CALLED
   ↓
IN_CONSULTATION
   ↓
COMPLETED
```

Possible exceptional states:

```text
CANCELLED
ABANDONED
ERROR
```

The backend is the authoritative owner of session state.

---

## 5.1 Create Session

```http
POST /sessions
```

Creates a new patient intake session.

### Request

```json
{
  "department_id": "general-medicine"
}
```

### Response

```json
{
  "data": {
    "session_id": "sess_01J...",
    "status": "CREATED",
    "department_id": "general-medicine",
    "created_at": "2026-09-15T09:30:00Z"
  }
}
```

The patient does not need to provide their doctor assignment at this stage.

---

## 5.2 Get Session

```http
GET /sessions/{session_id}
```

Returns the current session state.

### Response

```json
{
  "data": {
    "session_id": "sess_01J...",
    "status": "HISTORY_IN_PROGRESS",
    "department_id": "general-medicine",
    "verification_status": "VERIFIED",
    "consent_status": "GRANTED"
  }
}
```

The patient application should use this endpoint to recover state after a temporary connection failure or page refresh.

---

# 6. Patient Verification

Aurora uses **patient verification** as the kiosk UX concept.

The underlying implementation may eventually use ABHA or another hospital-approved identity mechanism.

The exact external identity mechanism must not leak into the patient application's core contract.

---

## 6.1 Start Verification

```http
POST /sessions/{session_id}/verification
```

### Request

The exact verification method is implementation-dependent.

Example:

```json
{
  "method": "ABHA",
  "identifier": "XXXX-XXXX-XXXX"
}
```

### Response

```json
{
  "data": {
    "verification_id": "ver_01J...",
    "status": "VERIFIED"
  }
}
```

Possible statuses:

```text
PENDING
VERIFIED
FAILED
EXPIRED
```

---

## 6.2 Get Verification Status

```http
GET /sessions/{session_id}/verification
```

### Response

```json
{
  "data": {
    "status": "VERIFIED",
    "verified_at": "2026-09-15T09:32:00Z"
  }
}
```

---

# 7. Consent

Consent must be obtained after patient verification and before clinical information is collected.

Consent covers the collection and processing of information required to prepare the patient's clinical history and consultation summary.

The final legal wording should be approved separately.

---

## 7.1 Get Consent Information

```http
GET /sessions/{session_id}/consent
```

### Response

```json
{
  "data": {
    "version": "1.0",
    "status": "PENDING",
    "text": "Consent text approved for the current deployment.",
    "audio_available": true,
    "supported_languages": [
      "en",
      "hi",
      "od"
    ]
  }
}
```

The patient UI may provide the consent explanation through text and/or pre-recorded audio.

---

## 7.2 Grant Consent

```http
POST /sessions/{session_id}/consent
```

### Request

```json
{
  "version": "1.0",
  "granted": true
}
```

### Response

```json
{
  "data": {
    "status": "GRANTED",
    "granted_at": "2026-09-15T09:33:00Z"
  }
}
```

If consent is denied:

```json
{
  "data": {
    "status": "DENIED"
  }
}
```

The backend must not begin clinical data collection when required consent has not been granted.

---

# 8. Clinical Conversation

The patient may interact through:

- Speech
- Text
- Guided touchscreen controls

The patient application should not need to know which AI model, speech-recognition system, or language model processes the interaction.

---

## 8.1 Submit Conversation Turn

```http
POST /sessions/{session_id}/conversation/turns
```

### Request

```json
{
  "input_type": "TEXT",
  "content": "I have had fever and cough for three days.",
  "language": "en"
}
```

Possible input types:

```text
TEXT
AUDIO
GUIDED_INPUT
```

### Response

```json
{
  "data": {
    "turn_id": "turn_01J...",
    "status": "PROCESSED",
    "response": {
      "type": "TEXT",
      "content": "How high has your fever been?"
    }
  }
}
```

For audio input, the uploaded audio itself is handled through the appropriate media/upload endpoint rather than embedding large binary data in JSON.

---

## 8.2 Get Conversation

```http
GET /sessions/{session_id}/conversation
```

Returns the conversation required by the current authorized client.

### Response

```json
{
  "data": {
    "turns": [
      {
        "turn_id": "turn_01J...",
        "speaker": "PATIENT",
        "input_type": "TEXT",
        "content": "I have had fever and cough for three days.",
        "language": "en",
        "created_at": "2026-09-15T09:34:00Z"
      },
      {
        "turn_id": "turn_01J...",
        "speaker": "SYSTEM",
        "input_type": "TEXT",
        "content": "How high has your fever been?",
        "language": "en",
        "created_at": "2026-09-15T09:34:03Z"
      }
    ]
  }
}
```

---

# 9. Documents

Patients may provide previous medical documents.

Supported document types may include:

```text
PDF
IMAGE
DOCUMENT
```

The actual OCR/image-processing implementation belongs to `backend/ai/`.

---

## 9.1 Upload Document

```http
POST /sessions/{session_id}/documents
```

Content type:

```text
multipart/form-data
```

Example fields:

```text
file=<document>
document_type=MEDICAL_RECORD
```

### Response

```json
{
  "data": {
    "document_id": "doc_01J...",
    "status": "UPLOADED",
    "filename": "previous_report.pdf"
  }
}
```

Possible processing states:

```text
UPLOADED
PROCESSING
PROCESSED
FAILED
```

---

## 9.2 Get Documents

```http
GET /sessions/{session_id}/documents
```

### Response

```json
{
  "data": [
    {
      "document_id": "doc_01J...",
      "filename": "previous_report.pdf",
      "status": "PROCESSED",
      "uploaded_at": "2026-09-15T09:40:00Z"
    }
  ]
}
```

---

## 9.3 Get Document Processing Status

```http
GET /documents/{document_id}
```

### Response

```json
{
  "data": {
    "document_id": "doc_01J...",
    "status": "PROCESSED",
    "extraction_status": "COMPLETED"
  }
}
```

---

# 10. Clinical Summary

The clinical summary is the structured representation prepared for the doctor.

It may combine information from:

- Patient conversation
- Guided inputs
- Previous medical documents
- Structured clinical extraction

The summary is **AI-assisted**, but it is not considered final until reviewed by the doctor.

---

## 10.1 Get Session Summary

```http
GET /sessions/{session_id}/summary
```

### Response

```json
{
  "data": {
    "summary_id": "sum_01J...",
    "session_id": "sess_01J...",
    "status": "READY",
    "chief_complaint": "Fever and cough",
    "history_of_present_illness": "...",
    "past_medical_history": [],
    "medications": [],
    "allergies": [],
    "relevant_documents": [],
    "clinical_signals": [],
    "generated_at": "2026-09-15T09:45:00Z"
  }
}
```

The exact clinical fields are expected to evolve with clinical-team review.

---

## 10.2 Doctor Review Summary

```http
PATCH /sessions/{session_id}/summary
```

Requires authenticated doctor access to the case.

### Request

```json
{
  "chief_complaint": "Fever and cough for 3 days",
  "history_of_present_illness": "...",
  "medications": [],
  "allergies": []
}
```

The doctor may edit or correct AI-generated information.

---

## 10.3 Confirm Summary

```http
POST /sessions/{session_id}/summary/confirm
```

### Response

```json
{
  "data": {
    "status": "CONFIRMED",
    "confirmed_by": "doctor_01J...",
    "confirmed_at": "2026-09-15T10:02:00Z"
  }
}
```

The system must retain the distinction between AI-generated information and doctor-confirmed information.

---

# 11. Clinical Signals and Triage

Aurora separates:

```text
AI signal extraction
        ↓
Clinical triage policy
        ↓
Queue scheduling
```

The AI layer may identify structured clinical signals.

The backend policy engine determines the operational urgency classification according to predefined rules.

The AI must not directly determine an arbitrary queue position.

---

## 11.1 Clinical Signals

Internal/backend representation may include:

```json
{
  "signal_type": "SYMPTOM",
  "name": "fever",
  "value": true,
  "confidence": 0.94,
  "source": "conversation"
}
```

Signals may also represent:

```text
SYMPTOM
DURATION
MEDICATION
ALLERGY
VITAL
HISTORY
RED_FLAG
OTHER
```

These are backend/domain objects and do not require a public patient-facing endpoint.

---

# 12. Priority

Aurora maintains two representations of urgency:

### Clinical urgency

A human-readable urgency level on a small fixed scale.

```text
1–5
```

The final clinical labels are subject to clinical-team review.

### Internal priority score

```text
0–100
```

This score is an internal scheduling representation.

It should not normally be shown to patients.

The score must not be interpreted as a diagnosis.

---

## 12.1 Get Triage Result

```http
GET /sessions/{session_id}/triage
```

### Response

```json
{
  "data": {
    "urgency_level": 3,
    "priority_score": 62,
    "red_flags_present": false,
    "status": "ASSESSED"
  }
}
```

The exact calculation remains a backend policy concern.

The API contract intentionally does not expose the internal rule implementation.

---

# 13. Queue

Aurora uses a **department-wide patient-centric queue**.

The department queue is the authoritative queue.

Doctor-specific queues are derived views of the department queue and are not independent sources of truth.

For the current MVP:

```text
General Medicine
```

is the primary department.

---

## 13.1 Get Department Queue

```http
GET /departments/{department_id}/queue
```

### Query parameters

```text
status
doctor_id
limit
cursor
```

Example:

```http
GET /departments/general-medicine/queue?status=WAITING
```

### Response

```json
{
  "data": [
    {
      "queue_entry_id": "queue_01J...",
      "position": 1,
      "session_id": "sess_01J...",
      "patient": {
        "display_name": "A. Kumar",
        "initials": "AK",
        "age": 21
      },
      "summary": {
        "brief": "Fever and cough"
      },
      "urgency_level": 4,
      "waiting_time_seconds": 420,
      "doctor_id": "doctor_01J...",
      "status": "WAITING"
    }
  ],
  "meta": {
    "total": 12
  }
}
```

### Important

`position` is calculated by the backend.

The frontend must not independently sort patients.

The doctor UI renders the ordered list received from the backend.

---

# 14. Queue Entry

A queue entry represents the patient's position within a department's operational queue.

Possible states:

```text
WAITING
PROMOTION_PENDING
READY
CALLED
IN_CONSULTATION
COMPLETED
CANCELLED
```

---

## 14.1 Get Queue Entry

```http
GET /queue/{queue_entry_id}
```

### Response

```json
{
  "data": {
    "queue_entry_id": "queue_01J...",
    "session_id": "sess_01J...",
    "department_id": "general-medicine",
    "status": "WAITING",
    "position": 4,
    "urgency_level": 3,
    "priority_score": 57,
    "waiting_time_seconds": 810,
    "doctor_id": "doctor_01J..."
  }
}
```

---

# 15. Doctor Assignment

Doctor assignment is a backend responsibility.

The system considers factors such as:

- Department eligibility
- Doctor availability
- Current workload
- Queue position
- Clinical urgency
- Waiting time

The patient does not need to know the internal assignment logic.

---

## 15.1 Get Assigned Doctor

```http
GET /sessions/{session_id}/assignment
```

### Response

```json
{
  "data": {
    "assignment_id": "assign_01J...",
    "doctor_id": "doctor_01J...",
    "department_id": "general-medicine",
    "status": "ACTIVE"
  }
}
```

This endpoint is primarily intended for authorized staff/doctor applications.

The patient application does not need to expose this information.

---

# 16. Doctor Cases

The doctor application retrieves cases assigned to the authenticated doctor.

---

## 16.1 Get Doctor Queue

```http
GET /doctors/me/queue
```

### Response

```json
{
  "data": [
    {
      "queue_entry_id": "queue_01J...",
      "session_id": "sess_01J...",
      "patient": {
        "display_name": "A. Kumar",
        "initials": "AK",
        "age": 21
      },
      "summary": {
        "brief": "Fever and cough for three days"
      },
      "urgency_level": 3,
      "waiting_time_seconds": 810,
      "status": "WAITING"
    }
  ]
}
```

This is a filtered view of the department queue.

---

## 16.2 Get Doctor Case

```http
GET /doctors/me/cases/{session_id}
```

### Response

```json
{
  "data": {
    "session": {},
    "patient": {},
    "summary": {},
    "documents": [],
    "triage": {},
    "assignment": {}
  }
}
```

The backend must verify that the authenticated doctor is authorized to access the requested case.

---

# 17. Patient Calling

Calling a patient is an operational action.

The patient does not need to know their queue position or internal scheduling state.

---

## 17.1 Call Patient

```http
POST /queue/{queue_entry_id}/call
```

### Response

```json
{
  "data": {
    "status": "CALLED",
    "called_at": "2026-09-15T10:15:00Z"
  }
}
```

---

## 17.2 Start Consultation

```http
POST /sessions/{session_id}/consultation/start
```

### Response

```json
{
  "data": {
    "status": "IN_CONSULTATION",
    "started_at": "2026-09-15T10:17:00Z"
  }
}
```

---

## 17.3 Complete Consultation

```http
POST /sessions/{session_id}/consultation/complete
```

### Response

```json
{
  "data": {
    "status": "COMPLETED",
    "completed_at": "2026-09-15T10:30:00Z"
  }
}
```

---

# 18. Promotion

Promotion allows an eligible patient to move ahead of the normal queue ordering when operationally required.

Automatic promotion is the default mechanism.

Administrative/reception staff may override the automatic action.

The promotion mechanism must not allow administrative inactivity to indefinitely block a clinically urgent case.

---

## 18.1 Create Promotion Request

```http
POST /queue/{queue_entry_id}/promotion
```

### Request

```json
{
  "reason": "Clinical urgency detected"
}
```

### Response

```json
{
  "data": {
    "promotion_request_id": "promo_01J...",
    "status": "PENDING",
    "decision_deadline": "2026-09-15T10:20:00Z"
  }
}
```

---

## 18.2 Get Promotion Request

```http
GET /promotion/{promotion_request_id}
```

### Response

```json
{
  "data": {
    "promotion_request_id": "promo_01J...",
    "queue_entry_id": "queue_01J...",
    "status": "PENDING",
    "decision_deadline": "2026-09-15T10:20:00Z"
  }
}
```

Possible statuses:

```text
PENDING
APPROVED
DENIED
AUTO_APPROVED
EXPIRED
CANCELLED
```

---

## 18.3 Approve Promotion

```http
POST /promotion/{promotion_request_id}/approve
```

### Request

```json
{
  "reason": "Approved by reception"
}
```

### Response

```json
{
  "data": {
    "status": "APPROVED",
    "decided_by": "admin_01J...",
    "decided_at": "2026-09-15T10:19:20Z"
  }
}
```

---

## 18.4 Deny Promotion

```http
POST /promotion/{promotion_request_id}/deny
```

### Request

```json
{
  "reason": "Promotion not required"
}
```

### Response

```json
{
  "data": {
    "status": "DENIED",
    "decided_by": "admin_01J...",
    "decided_at": "2026-09-15T10:19:30Z"
  }
}
```

---

## 18.5 Automatic Decision

If the administrative decision window expires, the backend promotion policy determines the resulting action.

The frontend must not implement the timeout itself as the authoritative mechanism.

Example:

```text
Promotion requested
        ↓
60-second decision window
        ↓
Admin approves → APPROVED
Admin denies   → DENIED
No decision   → policy-defined automatic action
```

The backend records the actual method used.

---

# 19. Admin / Reception Queue

The admin application is operational rather than clinical.

It provides:

- Department queue visibility
- Patient/doctor assignment visibility
- Promotion requests
- Promotion approval/denial
- Operational status

It does not provide a full clinical patient viewer.

---

## 19.1 Get Operational Queue

```http
GET /admin/departments/{department_id}/queue
```

### Response

```json
{
  "data": [
    {
      "queue_entry_id": "queue_01J...",
      "patient": {
        "display_name": "A. Kumar"
      },
      "doctor": {
        "display_name": "Dr. X"
      },
      "urgency_level": 3,
      "position": 4,
      "status": "WAITING"
    }
  ]
}
```

---

## 19.2 Get Pending Promotions

```http
GET /admin/promotions?status=PENDING
```

### Response

```json
{
  "data": [
    {
      "promotion_request_id": "promo_01J...",
      "queue_entry_id": "queue_01J...",
      "reason": "Clinical urgency detected",
      "decision_deadline": "2026-09-15T10:20:00Z",
      "remaining_seconds": 38
    }
  ]
}
```

`remaining_seconds` is informational.

The backend remains authoritative for the actual deadline.

---

# 20. Departments

---

## 20.1 List Departments

```http
GET /departments
```

### Response

```json
{
  "data": [
    {
      "department_id": "general-medicine",
      "name": "General Medicine",
      "status": "ACTIVE"
    }
  ]
}
```

General Medicine is the initial MVP department.

Future specialty routing may be introduced later.

---

# 21. Doctors

---

## 21.1 List Available Doctors

```http
GET /departments/{department_id}/doctors
```

### Response

```json
{
  "data": [
    {
      "doctor_id": "doctor_01J...",
      "display_name": "Dr. A",
      "availability": "AVAILABLE"
    }
  ]
}
```

This endpoint is primarily intended for authorized operational clients.

Patients do not need to select their doctor.

---

# 22. External Healthcare Integrations

Aurora separates external healthcare integrations from the core application.

Current implementation:

```text
backend/integrations/
├── abha/
├── fhir/
└── his/
```

The initial implementation may use mocks.

The frontend should communicate with Aurora's API rather than directly with ABHA, FHIR servers, or the hospital HIS.

---

# 23. ABHA Integration

The ABHA integration is responsible for identity-related interoperability.

The application layer should depend on an abstraction rather than a specific ABHA implementation.

Example internal interface:

```python
class ABHAProvider:
    async def verify_patient(...):
        ...
```

The concrete implementation may initially be a mock provider.

---

## 23.1 Mock ABHA Verification

The mock provider may expose internal test functionality such as:

```http
POST /integrations/mock/abha/verify
```

Example:

```json
{
  "identifier": "TEST-12345"
}
```

Response:

```json
{
  "verified": true,
  "patient_reference": "patient_mock_001"
}
```

This endpoint is for development/testing and must not be treated as the production ABHA API.

---

# 24. FHIR Integration

FHIR integration provides a boundary for exchanging structured healthcare information.

Aurora should internally convert its domain models to/from FHIR resources where required.

The rest of the application should not depend directly on FHIR JSON structures.

Example internal boundary:

```python
class FHIRProvider:
    async def get_patient(...):
        ...

    async def create_clinical_summary(...):
        ...

    async def link_session(...):
        ...
```

The initial provider may be a mock implementation.

---

# 25. HIS Integration

The HIS integration provides the hospital-system boundary.

Example internal interface:

```python
class HISProvider:
    async def get_patient(...):
        ...

    async def push_summary(...):
        ...

    async def update_consultation_status(...):
        ...
```

The production implementation will depend on the hospital's actual HIS interface.

---

# 26. Integration Principle

External healthcare systems must not leak into Aurora's core domain logic.

Preferred architecture:

```text
                 Aurora API
                     │
                     ▼
              Application Layer
                     │
                     ▼
               Domain Layer
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
      AI Boundary         Integration Boundary
   backend/ai/          backend/integrations/
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                  ABHA      FHIR       HIS
                  Mock      Mock       Mock
```

Replacing a mock integration with a production integration should not require rewriting the queue, session, or clinical domain logic.

---

# 27. AI Boundary

The public API intentionally does not expose model-provider-specific operations.

The application should not contain endpoints such as:

```text
POST /openai/...
POST /anthropic/...
POST /gemini/...
```

Instead, Aurora exposes domain-level operations.

For example:

```text
Conversation
    ↓
Clinical conversation service
    ↓
AI service boundary
    ↓
Model/provider selected by AI implementation
```

The AI implementation belongs under:

```text
backend/ai/
```

This includes, where required:

- Speech-to-text
- Text-to-speech
- OCR
- Image/document processing
- Clinical language processing
- Structured information extraction
- Clinical signal extraction
- Red-flag signal detection
- AI-generated clinical summaries

The exact AI dependencies are owned by the AI implementation and are not part of the core backend API contract.

---

# 28. Triage Boundary

Triage is intentionally split into two responsibilities.

```text
Patient interaction
        ↓
AI extraction
        ↓
Structured clinical signals
        ↓
Deterministic triage policy
        ↓
Urgency + priority
        ↓
Queue scheduler
```

The AI layer may say:

```json
{
  "red_flags": [
    "..."
  ]
}
```

The policy engine decides what those signals mean operationally.

This separation allows clinical rules to be reviewed and changed independently of the AI model.

---

# 29. Queue Ordering

The queue scheduler is backend-owned.

A simplified conceptual ordering model is:

```text
Clinical urgency
        +
Priority policy
        +
Waiting-time fairness
        +
Operational constraints
        ↓
Ordered department queue
```

The exact algorithm is an implementation/domain concern.

Frontend applications must never calculate queue position themselves.

---

# 30. Real-Time Updates

The initial implementation may use normal HTTP polling.

If real-time behavior becomes necessary, Aurora may introduce:

```text
WebSocket
```

or:

```text
Server-Sent Events
```

without changing the underlying resource model.

Potential real-time events include:

```text
QUEUE_UPDATED
PATIENT_CALLED
PROMOTION_CREATED
PROMOTION_UPDATED
ASSIGNMENT_CHANGED
SESSION_STATUS_CHANGED
```

The backend remains authoritative even when events are delivered through a real-time channel.

---

# 31. Idempotency

Operations that may be retried by the frontend should be designed to avoid unintended duplicate state transitions.

Examples include:

```text
Consent submission
Document upload
Promotion decision
Consultation start
Consultation completion
```

Where necessary, an idempotency key may be supplied:

```http
Idempotency-Key: <unique-request-id>
```

The backend determines whether an operation has already been processed.

---

# 32. State Transition Rules

The backend owns lifecycle transitions.

The frontend must not directly assign arbitrary states.

For example, the patient frontend should not send:

```json
{
  "status": "QUEUED"
}
```

to force a session into the queue.

Instead, the backend transitions the session when its prerequisites are satisfied.

Example:

```text
VERIFIED
   +
CONSENTED
   +
HISTORY_COMPLETE
   +
DOCUMENT_PROCESSING_COMPLETE
   +
SUMMARY_READY
        ↓
      QUEUED
```

---

# 33. Auditability

Operationally significant actions should be auditable.

Examples:

- Patient verification
- Consent
- Summary confirmation
- Doctor assignment
- Promotion creation
- Promotion approval
- Promotion denial
- Automatic promotion
- Consultation start
- Consultation completion

An audit record should contain information such as:

```json
{
  "action": "PROMOTION_APPROVED",
  "actor_id": "admin_01J...",
  "actor_role": "ADMIN",
  "resource_id": "promo_01J...",
  "timestamp": "2026-09-15T10:19:20Z",
  "reason": "Approved by reception"
}
```

Audit implementation is backend-owned.

---

# 34. Patient Privacy

Patient-facing APIs should expose only the information necessary for the current session.

The patient should not receive:

- Internal queue position
- Other patients' information
- Internal priority score
- Other patients' clinical information
- Internal doctor workload
- Internal promotion decisions unrelated to the patient
- Internal AI processing details

Doctor and admin access must be enforced by backend authorization.

---

# 35. API Ownership

| Area | Owner |
|---|---|
| Session lifecycle | Backend/domain |
| Verification | Backend + integration |
| Consent | Backend/domain |
| Conversation | Backend + AI boundary |
| OCR | AI boundary |
| Speech | AI boundary |
| Clinical extraction | AI boundary |
| Clinical signals | AI boundary/domain |
| Triage policy | Backend/domain |
| Queue ordering | Backend/domain |
| Doctor assignment | Backend/domain |
| Promotion | Backend/domain |
| Doctor review | Backend |
| Patient UI | Patient frontend |
| Doctor UI | Doctor frontend |
| Admin UI | Admin frontend |
| ABHA | Integration boundary |
| FHIR | Integration boundary |
| HIS | Integration boundary |

---

# 36. MVP Scope

The first implementation should support:

```text
Patient verification
        ↓
Consent
        ↓
Clinical conversation
        ↓
Document upload
        ↓
Clinical summary
        ↓
Triage
        ↓
General Medicine queue
        ↓
Doctor assignment
        ↓
Doctor review
        ↓
Patient calling
        ↓
Consultation
```

Administrative promotion control is also part of the MVP operational flow.

---

# 37. Deferred Features

The following are intentionally not required to be fully implemented initially:

- Multi-specialty routing
- Automatic specialist selection
- Production ABHA integration
- Production HIS integration
- Production FHIR interoperability
- Advanced real-time infrastructure
- Complex hospital scheduling
- Full patient medical-record viewer
- Advanced analytics
- Large-scale audit/reporting UI

The API should remain extensible enough to support these later.

---

# 38. Design Principle

Aurora's API should expose **clinical and operational capabilities**, not implementation details.

Good:

```http
POST /sessions/{id}/conversation/turns
```

Not:

```http
POST /gemini/generate
```

Good:

```http
GET /departments/{id}/queue
```

Not:

```http
GET /redis/sorted-set
```

Good:

```http
POST /queue/{id}/promotion
```

Not:

```http
POST /priority-score/increment
```

The API describes **what Aurora does**, while backend modules decide **how Aurora does it**.

This keeps the patient, doctor, and admin applications independent from AI providers, database implementation, queue algorithms, and healthcare-system integrations.

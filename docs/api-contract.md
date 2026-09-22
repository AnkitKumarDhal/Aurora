# Aurora API Contracts

This document describes the HTTP API exposed by the Aurora backend.

The implementation is currently versioned under:

```text
/api/v1
```

The backend is the authoritative owner of application state, authorization, queue ordering, triage policy and workflow transitions.

The examples in this document are representative contracts based on the current implementation.

---

# 1. Base URL

Local development:

```text
http://localhost:8000/api/v1
```

The frontend Vite development servers proxy:

```text
/api/*
```

to the backend.

---

# 2. Authentication

Aurora currently has two authenticated staff roles:

```text
DOCTOR
ADMIN
```

The patient kiosk does not use a normal staff-style login.

Staff APIs use:

```http
Authorization: Bearer <access_token>
```

The backend enforces authorization independently of frontend visibility.

---

# 3. Response Conventions

Most successful responses wrap their payload in:

```json
{
  "data": {}
}
```

Collections commonly use:

```json
{
  "data": []
}
```

Some workflows additionally return:

```json
{
  "data": {},
  "meta": {}
}
```

---

# 4. Error Responses

Current FastAPI routes generally return FastAPI-style errors.

Example:

```json
{
  "detail": "Clinical session not found"
}
```

Common HTTP statuses include:

| Status | Meaning |
|---|---|
| `200` | Successful request |
| `201` | Resource created |
| `400` | Invalid request / invalid workflow state |
| `401` | Authentication required or invalid |
| `403` | Authenticated but not authorized |
| `404` | Resource not found |
| `409` | State conflict |
| `422` | Request validation failure |
| `500` | Internal server failure |
| `503` | External/mock service unavailable |

---

# 5. Sessions

## Create Session

```http
POST /api/v1/sessions
```

Request:

```json
{
  "department_id": "general-medicine"
}
```

Response:

```json
{
  "data": {
    "session_id": "sess_abc123",
    "patient_id": "unverified",
    "department_id": "general-medicine",
    "status": "CREATED",
    "verification_status": "PENDING",
    "consent_status": "PENDING",
    "created_at": "2026-09-21T10:00:00Z",
    "updated_at": "2026-09-21T10:00:00Z"
  }
}
```

---

## Get Session

```http
GET /api/v1/sessions/{session_id}
```

Returns the current clinical session state.

---

## Abandon Session

```http
POST /api/v1/sessions/{session_id}/abandon
```

Used when an intake session is abandoned.

---

# 6. Patient Verification

Aurora currently supports a kiosk-oriented identity verification flow using an ephemeral verification service and a mock identity provider in demo mode.

## Request OTP

```http
POST /api/v1/identity/otp
```

Request:

```json
{
  "draft_id": "draft_123",
  "method": "ABHA",
  "identifier": "11112222333344"
}
```

Response:

```json
{
  "data": {
    "challenge_id": "otp_123",
    "masked_destination": "registered mobile number",
    "expires_in_seconds": 300,
    "demo_otp": "123456"
  }
}
```

The `demo_otp` field is provided only when the mock identity provider is running in demo mode.

---

## Verify OTP

```http
POST /api/v1/identity/otp/verify
```

Request:

```json
{
  "draft_id": "draft_123",
  "challenge_id": "otp_123",
  "otp": "123456"
}
```

Response:

```json
{
  "data": {
    "verification_token": "ver_123",
    "status": "VERIFIED",
    "expires_in_seconds": 900
  }
}
```

The verification token is temporary and is used by later patient-intake operations.

---

# 7. Session Verification APIs

The backend also exposes session-scoped verification endpoints.

## Request OTP

```http
POST /api/v1/sessions/{session_id}/verification/otp
```

Request:

```json
{
  "method": "ABHA",
  "identifier": "11112222333344"
}
```

Response:

```json
{
  "data": {
    "challenge_id": "otp_123",
    "masked_destination": "registered mobile number",
    "expires_in_seconds": 300,
    "demo_otp": "123456"
  }
}
```

---

## Verify Identity

```http
POST /api/v1/sessions/{session_id}/verification
```

Request:

```json
{
  "challenge_id": "otp_123",
  "otp": "123456"
}
```

Response contains the verification result and whether the identity corresponds to an existing patient.

---

## Get Verification

```http
GET /api/v1/sessions/{session_id}/verification
```

---

# 8. Consent

## Get Consent Status

```http
GET /api/v1/sessions/{session_id}/consent
```

Returns the session consent state and consent information.

---

## Record Consent

```http
POST /api/v1/sessions/{session_id}/consent
```

Request:

```json
{
  "version": "1.0",
  "granted": true,
  "method": "ABHA",
  "identifier": "11112222333344"
}
```

Response:

```json
{
  "data": {
    "version": "1.0",
    "consent_status": "GRANTED",
    "recorded_at": "2026-09-21T10:05:00Z"
  },
  "meta": {
    "session_status": "CONSENTED"
  }
}
```

---

## Get Localized Consent Information

```http
GET /api/v1/consent-information?language=en
```

Supported patient languages currently include:

```text
en
hi
```

Example:

```http
GET /api/v1/consent-information?language=hi
```

Response:

```json
{
  "data": {
    "version": "1.0",
    "status": "AVAILABLE",
    "text": "वर्तमान तैनाती के लिए स्वीकृत सहमति पाठ।",
    "audio_available": true,
    "supported_languages": [
      "en",
      "hi",
      "od"
    ]
  }
}
```

---

# 9. Interview Session Preparation

## Prepare Interview Session

```http
POST /api/v1/patient-intake/interview/session
```

Request:

```json
{
  "draft_id": "draft_123",
  "verification_token": "ver_123",
  "identity_method": "ABHA",
  "identity_identifier": "11112222333344",
  "department_id": "general-medicine"
}
```

Response:

```json
{
  "data": {
    "session_id": "sess_123",
    "status": "HISTORY_IN_PROGRESS",
    "verification_status": "VERIFIED",
    "consent_status": "GRANTED"
  }
}
```

---

# 10. AI Interview

## Get Interview State

```http
GET /api/v1/sessions/{session_id}/interview
```

Response:

```json
{
  "data": {
    "session_id": "sess_123",
    "topic": "headache",
    "known_fields": {
      "severity": 7
    },
    "patient_turns": 2,
    "next_question": "Where exactly do you feel it?",
    "completed": false,
    "red_flags": [],
    "ai_enabled": true
  }
}
```

---

## Submit Interview Turn

```http
POST /api/v1/sessions/{session_id}/interview/turns
```

Request:

```json
{
  "draft_id": "draft_123",
  "client_turn_id": "turn_3",
  "content": "The pain is in the middle of my head.",
  "input_type": "TEXT",
  "language": "en"
}
```

Supported input types:

```text
TEXT
AUDIO
GUIDED_INPUT
```

Response:

```json
{
  "data": {
    "turn_id": "turn_123",
    "session_id": "sess_123",
    "speaker": "patient",
    "input_type": "TEXT",
    "content": "The pain is in the middle of my head.",
    "language": "en",
    "created_at": "2026-09-21T10:10:00Z",
    "assistant_response": "How severe is the pain on a scale of 0 to 10?",
    "next_question": "How severe is the pain on a scale of 0 to 10?",
    "completed": false,
    "topic": "headache",
    "known_fields": {
      "site": "middle of head"
    },
    "extracted_fields": {
      "site": "middle of head"
    },
    "negative_fields": [],
    "red_flags": [],
    "ai_used": true
  }
}
```

---

## Finalize Interview

```http
POST /api/v1/sessions/{session_id}/interview/finalize
```

Returns the generated clinical summary and triage information.

---

# 11. Generic Conversation API

The conversation persistence layer is separate from the higher-level interview controller.

## Submit Conversation Turn

```http
POST /api/v1/sessions/{session_id}/conversation/turns
```

Request:

```json
{
  "input_type": "TEXT",
  "content": "I have had fever since yesterday.",
  "language": "en",
  "media_reference": null
}
```

Response:

```json
{
  "data": {
    "turn_id": "turn_123",
    "session_id": "sess_123",
    "speaker": "patient",
    "input_type": "TEXT",
    "content": "I have had fever since yesterday.",
    "language": "en",
    "media_reference": null,
    "created_at": "2026-09-21T10:11:00Z"
  }
}
```

---

## Get Conversation History

```http
GET /api/v1/sessions/{session_id}/conversation/turns
```

Requires authorized doctor access.

Response:

```json
{
  "data": {
    "turns": [
      {
        "turn_id": "turn_1",
        "session_id": "sess_123",
        "speaker": "patient",
        "input_type": "TEXT",
        "content": "I have had fever since yesterday.",
        "language": "en",
        "media_reference": null,
        "created_at": "2026-09-21T10:11:00Z"
      }
    ]
  }
}
```

The doctor UI uses this history for conversation auditing.

---

# 12. Documents

## Upload Patient Document

```http
POST /api/v1/sessions/{session_id}/documents
```

Content type:

```text
multipart/form-data
```

Typical fields:

```text
document_type=MEDICAL_RECORD
file=<binary file>
```

Supported document categories are represented by the `DocumentType` enum.

Current application values include:

```text
IMAGING_REPORT
LAB_REPORT
MEDICAL_RECORD
OTHER
PRESCRIPTION
```

Response:

```json
{
  "data": {
    "document_id": "doc_123",
    "session_id": "sess_123",
    "filename": "prescription.jpg",
    "document_type": "PRESCRIPTION",
    "content_type": "image/jpeg",
    "size_bytes": 245812,
    "storage_reference": "...",
    "status": "UPLOADED",
    "created_at": "2026-09-21T10:20:00Z",
    "updated_at": "2026-09-21T10:20:00Z"
  }
}
```

---

## List Session Documents

```http
GET /api/v1/sessions/{session_id}/documents
```

---

## Get Document

```http
GET /api/v1/sessions/{session_id}/documents/{document_id}
```

---

## Get Original Document File

```http
GET /api/v1/sessions/{session_id}/documents/{document_id}/file
```

Requires authorized doctor access.

The response is the original uploaded file.

For images:

```text
Content-Type: image/*
```

For PDFs:

```text
Content-Type: application/pdf
```

The doctor UI uses the returned binary file to render the source document for human verification.

---

## Get Document Extraction

```http
GET /api/v1/sessions/{session_id}/documents/{document_id}/extraction
```

Example:

```json
{
  "data": {
    "extraction_id": "extract_123",
    "document_id": "doc_123",
    "status": "PROCESSED",
    "extracted_text": "Patient: ...",
    "structured_data": {
      "patient_name": "Example Patient",
      "medications": [
        "Paracetamol 500 mg"
      ]
    },
    "processed_at": "2026-09-21T10:21:00Z",
    "created_at": "2026-09-21T10:21:00Z",
    "updated_at": "2026-09-21T10:21:00Z"
  }
}
```

The original source file and extracted representation are deliberately kept separate.

---

# 13. Patient Registration

## Submit Patient Intake

```http
POST /api/v1/patient-intake/submit
```

Content type:

```text
multipart/form-data
```

The request contains:

```text
draft
documents
files
```

The `draft` contains patient-intake information including:

```json
{
  "version": 1,
  "draft_id": "draft_123",
  "language": "hi",
  "identity_method": "ABHA",
  "identity_identifier": "11112222333344",
  "verification_token": "ver_123",
  "consent_version": "1.0",
  "consent_granted": true,
  "conversation_turns": []
}
```

Response:

```json
{
  "data": {
    "session_id": "sess_123",
    "patient_id": "patient_123",
    "status": "SUMMARY_READY",
    "visit_type": "FIRST_VISIT"
  }
}
```

---

## Complete Patient Intake

```http
POST /api/v1/patient-intake/complete
```

Request:

```json
{
  "session_id": "sess_123",
  "draft_id": "draft_123",
  "verification_token": "ver_123",
  "identity_method": "ABHA",
  "identity_identifier": "11112222333344"
}
```

This completes the intake workflow and queues/assigns the patient.

Response:

```json
{
  "data": {
    "session_id": "sess_123",
    "status": "ASSIGNED",
    "queue_entry_id": "queue_123",
    "doctor_id": "doctor_123"
  }
}
```

---

# 14. Clinical Summary

All summary endpoints require authorized doctor access.

## Get Summary

```http
GET /api/v1/sessions/{session_id}/summary
```

---

## Create Summary

```http
POST /api/v1/sessions/{session_id}/summary
```

The backend accepts structured clinical-summary fields such as:

```json
{
  "chief_complaint": "Fever and cough",
  "history_of_present_illness": "Symptoms for three days",
  "past_medical_history": [],
  "medications": [],
  "allergies": [],
  "relevant_documents": [],
  "clinical_signals": [],
  "generated_at": "2026-09-21T10:30:00Z"
}
```

---

## Update Summary

```http
PATCH /api/v1/sessions/{session_id}/summary
```

Used by the doctor to correct AI-generated information.

Only provided fields are updated.

---

## Confirm Summary

```http
POST /api/v1/sessions/{session_id}/summary/confirm
```

Example response:

```json
{
  "data": {
    "summary_id": "summary_123",
    "session_id": "sess_123",
    "status": "CONFIRMED",
    "confirmed_by": "doctor_123",
    "confirmed_at": "2026-09-21T10:35:00Z"
  }
}
```

---

# 15. Clinical Intelligence

## Get Clinical Intelligence

```http
GET /api/v1/sessions/{session_id}/clinical-intelligence
```

This endpoint builds the current clinical-intelligence view for an authorized doctor.

It combines backend clinical information without exposing the internal AI implementation details.

---

# 16. Triage

## Get Triage

```http
GET /api/v1/sessions/{session_id}/triage
```

Response:

```json
{
  "data": {
    "triage_id": "triage_123",
    "session_id": "sess_123",
    "status": "ASSESSED",
    "urgency_level": 3,
    "priority_score": 62,
    "red_flags_present": false,
    "assessed_at": "2026-09-21T10:36:00Z"
  }
}
```

---

## Assess Triage

```http
POST /api/v1/sessions/{session_id}/triage
```

Request:

```json
{
  "trigger": "manual"
}
```

The backend re-evaluates triage from the session's clinical signals.

---

# 17. Queue

## Get Department Queue

```http
GET /api/v1/queue/departments/{department_id}
```

Requires department access.

Response:

```json
{
  "data": [
    {
      "queue_entry_id": "queue_123",
      "session_id": "sess_123",
      "department_id": "general-medicine",
      "status": "WAITING",
      "position": 4,
      "urgency_level": 3,
      "priority_score": 62,
      "doctor_id": "doctor_123",
      "queued_at": "2026-09-21T10:40:00Z",
      "called_at": null,
      "completed_at": null
    }
  ]
}
```

The backend is responsible for queue ordering.

---

## Get Queue Entry

```http
GET /api/v1/queue/{queue_entry_id}
```

Requires access to the queue entry's department.

---

# 18. Assignment

## Get Session Assignment

```http
GET /api/v1/sessions/{session_id}/assignment
```

Requires authorized doctor access.

Example:

```json
{
  "data": {
    "assignment_id": "assignment_123",
    "session_id": "sess_123",
    "doctor_id": "doctor_123",
    "department_id": "general-medicine",
    "status": "ACTIVE",
    "assigned_at": "2026-09-21T10:41:00Z",
    "released_at": null
  }
}
```

---

# 19. Workflow Actions

These endpoints are the main workflow mutation APIs.

## Queue Session From Triage

```http
POST /api/v1/sessions/{session_id}/queue
```

The session must have a ready summary and triage information.

---

## Assign Patient

```http
POST /api/v1/sessions/{session_id}/queue/{queue_entry_id}/assign
```

Requires:

```text
ADMIN
```

The backend invokes the assignment scheduler.

---

## Call Patient

```http
POST /api/v1/sessions/{session_id}/queue/{queue_entry_id}/call
```

Requires:

```text
DOCTOR
```

The authenticated doctor must be the assigned doctor.

---

## Start Consultation

```http
POST /api/v1/sessions/{session_id}/queue/{queue_entry_id}/start-consultation
```

Requires:

```text
DOCTOR
```

The authenticated doctor must be the assigned doctor.

---

## Complete Consultation

```http
POST /api/v1/sessions/{session_id}/queue/{queue_entry_id}/complete
```

Requires:

```text
DOCTOR
```

Completion releases the active assignment and updates the clinical workflow state.

---

# 20. Doctor Queue

## Get Current Doctor Queue

```http
GET /api/v1/doctors/me/queue
```

Requires:

```text
DOCTOR
```

The backend filters the department queue to entries assigned to the authenticated doctor.

Each entry may include:

```json
{
  "queue_entry_id": "queue_123",
  "session_id": "sess_123",
  "position": 4,
  "urgency_level": 3,
  "waiting_time_seconds": 810,
  "doctor_id": "doctor_123",
  "status": "WAITING",
  "patient": {
    "patient_id": "patient_123",
    "display_name": "Example Patient",
    "age": 35
  },
  "summary": {}
}
```

---

# 21. Doctor Case

## Get Assigned Patient Case

```http
GET /api/v1/doctors/me/cases/{session_id}
```

Requires:

```text
DOCTOR
```

The backend verifies that the doctor has assignment history for the session.

Response:

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

---

# 22. Admin Dashboard

## Get Department Dashboard

```http
GET /api/v1/admin/departments/{department_id}/dashboard
```

Requires:

```text
ADMIN
```

Response contains:

```text
department_id
stats
doctors
patients
promotions
```

The dashboard statistics currently include:

```text
patients
waiting
in_consultation
doctors
```

Each doctor summary can include:

```text
doctor_id
display_name
status
assigned_count
```

Each patient operational record can include:

```text
queue_entry_id
session_id
patient_id
display_name
age
urgency_level
priority_score
queue_status
doctor_id
doctor_name
chief_complaint
queued_at
waiting_time_seconds
```

---

# 23. Promotions

## Get Pending Promotions

```http
GET /api/v1/promotions/pending
```

Requires:

```text
ADMIN
```

---

## Get Promotion

```http
GET /api/v1/promotions/{promotion_request_id}
```

Requires:

```text
ADMIN
```

---

## Create Manual Promotion

```http
POST /api/v1/promotions
```

Request:

```json
{
  "queue_entry_id": "queue_123",
  "target_doctor_id": "doctor_456",
  "reason": "Earlier attention may be available"
}
```

Requires:

```text
ADMIN
```

---

## Approve Promotion

```http
POST /api/v1/promotions/{promotion_request_id}/approve
```

Request:

```json
{
  "decision_reason": "Approved by reception"
}
```

---

## Deny Promotion

```http
POST /api/v1/promotions/{promotion_request_id}/deny
```

Request:

```json
{
  "decision_reason": "Promotion not required"
}
```

---

## Cancel Promotion

```http
POST /api/v1/promotions/{promotion_request_id}/cancel
```

---

# 24. Reassignment

## Reassign Patient

```http
POST /api/v1/admin/reassignments
```

Requires:

```text
ADMIN
```

Request:

```json
{
  "queue_entry_id": "queue_123",
  "doctor_id": "doctor_456"
}
```

Response:

```json
{
  "data": {
    "queue_entry_id": "queue_123",
    "session_id": "sess_123",
    "previous_doctor_id": "doctor_123",
    "doctor_id": "doctor_456",
    "assignment_id": "assignment_789"
  }
}
```

---

# 25. Real-Time Events

## SSE Stream

```http
GET /api/v1/events/stream?department_id=general-medicine
```

Authentication:

```http
Authorization: Bearer <access_token>
```

Supported authenticated roles:

```text
DOCTOR
ADMIN
```

Doctors are additionally checked for membership in the requested department.

The stream sends Server-Sent Events.

Example:

```text
id: event_123
event: QUEUE_UPDATED
data: {"id":"event_123","type":"QUEUE_UPDATED","department_id":"general-medicine","entity_id":"queue_123","timestamp":"2026-09-21T10:45:00+00:00"}
```

Current event types:

```text
QUEUE_UPDATED
ASSIGNMENT_UPDATED
PROMOTION_UPDATED
```

The stream also emits heartbeat comments when no domain event is available.

---

# 26. Integration Boundaries

The backend currently uses mock integrations for:

```text
Identity / ABHA
FHIR
HIS / EMR
```

These integrations are internal backend boundaries and are not intended to expose provider-specific details directly to the frontend applications.

---

# 27. Session Lifecycle

A typical clinical session moves through:

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

Possible exceptional states include:

```text
CANCELLED
ABANDONED
ERROR
```

The backend owns the authoritative transition rules.

---

# 28. Important Contract Principles

## Backend authority

The frontend does not determine:

- queue order
- triage urgency
- priority score
- assignment correctness
- promotion outcome
- authorization

---

## Doctor clinical control

AI-generated information can be:

```text
generated
→ reviewed
→ edited
→ confirmed
```

The doctor remains the final reviewer of the generated clinical summary.

---

## Source verification

Document extraction and the original source document remain independently available.

The doctor can compare:

```text
Original document
        ↕
OCR text
        ↕
Structured extraction
```

---

## Conversation verification

The doctor can compare:

```text
Patient statement
        ↓
AI response
        ↓
Extracted clinical fields
        ↓
Clinical summary
```

This provides a traceable audit path through the intake pipeline.

---

# 29. API Evolution

The API contract is expected to evolve as:

- the clinical workflow is refined
- real healthcare integrations are introduced
- additional languages are added
- document understanding improves
- clinical requirements are validated
- production security requirements are introduced

Backward compatibility should be considered for any change to an endpoint currently consumed by a frontend application.

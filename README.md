# Aurora

Aurora is an AI-assisted clinical intake and OPD workflow platform designed to move structured history-taking, document collection and initial prioritization to the beginning of the patient's hospital journey.

The goal is not to replace the doctor.

Aurora prepares a structured clinical context before the consultation so that the doctor can spend less time collecting repetitive information and more time reviewing, validating and treating the patient.

The current MVP focuses on a General Medicine OPD workflow.

---

## Product Flow

```text
Patient
   ↓
Patient Kiosk
   ↓
Language Selection
   ↓
Identity Verification
   ↓
Consent
   ↓
AI Clinical History
   ↓
Document Capture
   ↓
OCR / Document Extraction
   ↓
Structured Clinical Summary
   ↓
Clinical Signals
   ↓
Triage / Priority
   ↓
General Medicine Queue
   ↓
Doctor Assignment
   ↓
Doctor Review
   ↓
Consultation
   ↓
Completion
```

The patient uses a dedicated kiosk-oriented web interface.

Doctors use a separate authenticated clinical workspace.

Reception and administrative staff use a separate operational dashboard for queue monitoring and promotion decisions.

---

# Applications

Aurora is composed of three frontend applications and one backend:

```text
Aurora/
├── backend/
├── patient-web/
├── doctor-web/
└── admin-web/
```

## Patient Web

`patient-web/` is the kiosk application.

It is designed for patients rather than technical users and intentionally uses larger controls, simple language and touch-friendly interaction.

Current capabilities include:

- language selection
- English and Hindi patient flow support
- patient identity verification
- OTP verification in demo mode
- consent
- text-based clinical interaction
- voice-based clinical interaction
- browser microphone permission handling
- AI-assisted clinical history
- document capture
- intake completion

The patient application does not use a conventional username/password patient account.

Identity is verified through the kiosk flow and associated with the current clinical session.

---

## Doctor Web

`doctor-web/` is the authenticated clinical application.

It provides:

- doctor authentication
- doctor display-name identity
- General Medicine queue
- assigned patient view
- patient case review
- clinical summary
- AI-generated summary editing
- summary confirmation
- triage information
- patient identity information
- medical document review
- structured OCR extraction
- raw OCR text
- original source image/PDF viewing
- patient/AI conversation audit trail
- patient calling
- consultation workflow

The doctor remains responsible for reviewing and confirming AI-generated clinical information.

---

## Admin Web

`admin-web/` is the operational/reception interface.

It provides:

- department-wide queue visibility
- patient/doctor assignment visibility
- queue status
- doctor workload information
- promotion requests
- promotion approval/denial
- promotion timeout state
- operational dashboard statistics

The admin interface intentionally exposes less clinical detail than the doctor interface.

---

# Backend

The backend is the central application and system-of-record layer.

It is responsible for:

- HTTP APIs
- authentication
- authorization
- patient records
- clinical sessions
- conversation persistence
- document persistence
- document processing
- clinical signals
- clinical summaries
- triage policy
- queue management
- doctor assignment
- reassignment
- promotion workflows
- server-sent events
- healthcare integration boundaries

Frontend applications never access MongoDB directly.

```text
Patient Web ─┐
Doctor Web  ─┼──→ FastAPI Backend ───→ MongoDB
Admin Web   ─┘             │
                           ├── AI
                           ├── Storage
                           └── External Integration Boundaries
```

---

# AI Layer

AI-related functionality is isolated under:

```text
backend/ai/
```

The current architecture separates the AI layer from the core domain and workflow logic.

The AI layer currently includes functionality for areas such as:

- clinical conversation processing
- information extraction
- topic detection
- interview objective extraction
- clinical signal extraction
- red-flag detection
- document extraction
- OCR processing

The interview system supports a configurable LLM provider.

The current development configuration uses a Lemonade-compatible chat-completions endpoint with a configurable model.

Example configuration:

```text
AURORA_INTERVIEW_AI_PROVIDER=lemonade
AURORA_LEMONADE_URL=http://127.0.0.1:13305/api/v1/chat/completions
AURORA_LEMONADE_MODEL=qwen3.5-9b-FLM
```

The AI layer is not allowed to directly determine arbitrary queue positions.

The backend owns the workflow and policy decisions.

---

# Clinical Interview

The patient interview combines deterministic interview objectives with AI-assisted extraction.

The broad flow is:

```text
Patient Answer
      ↓
AI / Extraction Layer
      ↓
Structured Fields
      ↓
Known Clinical Fields
      ↓
Remaining Interview Objectives
      ↓
Next Relevant Question
```

The system currently supports:

- English
- Hindi

The selected patient language is propagated through the conversation and stored with the conversation turn.

The interview system can preserve explicit negative findings such as:

```text
fever → no
cough → no
breathing difficulty → no
```

Explicit negatives are treated as meaningful information rather than as missing information.

The interview system has a configured maximum follow-up limit that acts as a safety bound rather than as a substitute for clinical completeness.

---

# Voice Interaction

The patient application supports browser speech recognition.

The current voice flow is:

```text
Patient taps microphone
        ↓
Secure-context check
        ↓
Microphone permission preflight
        ↓
Browser permission prompt if required
        ↓
SpeechRecognition
        ↓
English / Hindi transcript
        ↓
Interview turn
        ↓
AI processing
```

English uses:

```text
en-US
```

Hindi uses:

```text
hi-IN
```

The application explicitly requests microphone permission using the browser media APIs before starting recognition.

Voice interaction currently persists the resulting transcript as a conversation turn.

The raw microphone audio is not persisted by the current conversation workflow.

For mobile devices, voice input requires a browser context where microphone access is permitted by the browser and deployment environment. HTTPS should be used for externally accessible deployments.

---

# Language Support

The patient flow currently supports:

```text
English
Hindi
```

Hindi support includes:

- patient-facing interface text
- interview questions
- consent information
- interview language propagation
- Hindi answer interpretation
- Hindi fallback extraction
- Hindi symptom/topic phrases
- Hindi voice recognition configuration

The architecture keeps language-specific behavior at the patient/AI interaction boundaries so that more languages can be added later.

---

# Documents and OCR

Patients can upload medical documents such as:

```text
Prescription
Medical Record
Laboratory Report
Imaging Report
Other
```

Documents are stored by the backend and processed asynchronously/through the document-processing layer.

The document workflow is:

```text
Patient Upload
      ↓
Original File Stored
      ↓
Document Record
      ↓
OCR / Extraction
      ↓
Raw Extracted Text
      ↓
Structured Data
      ↓
Doctor Review
```

The original source document is retained.

The doctor interface can view:

```text
┌───────────────────────────────┬─────────────────────────────┐
│ Structured extraction         │                             │
│                               │                             │
│ key → value                   │     Original source        │
│                               │     image / PDF             │
├───────────────────────────────┤                             │
│ Raw OCR text                  │                             │
│                               │                             │
└───────────────────────────────┴─────────────────────────────┘
```

This is intentional.

OCR is treated as an assistive extraction mechanism rather than as unquestionable ground truth.

Retaining the source document allows the doctor to verify:

- medication names
- dosage
- dates
- handwritten information
- values incorrectly recognized by OCR
- information omitted by OCR

---

# Doctor Conversation Audit

The doctor can view the exact persisted patient/AI conversation associated with the intake session.

The audit trail is intended to make it possible to see:

```text
AI Question
     ↓
Patient Answer
     ↓
Extracted Clinical Information
     ↓
Doctor Verification
```

This allows a doctor to identify cases where:

- the AI misunderstood the patient's answer
- the patient answered ambiguously
- the extracted field does not match the conversation
- the final summary omitted relevant information

The current implementation stores the conversation transcript and associated metadata such as:

- speaker
- input type
- language
- timestamp
- content

---

# Clinical Summary

Aurora generates a structured clinical summary from information gathered during intake.

The summary may include:

- chief complaint
- history of present illness
- past medical history
- medications
- allergies
- clinical signals
- relevant documents

The summary is AI-assisted.

It is not final until the doctor reviews and confirms it.

```text
AI-generated summary
        ↓
Doctor review
        ↓
Doctor edits if required
        ↓
Doctor confirmation
        ↓
Confirmed clinical summary
```

The system preserves the distinction between generated and confirmed information.

---

# Clinical Signals and Triage

Aurora separates information extraction from operational triage.

```text
Patient Conversation
        ↓
AI / NLP
        ↓
Structured Clinical Signals
        ↓
Triage Policy Engine
        ↓
Urgency
        ↓
Priority Score
        ↓
Queue
```

The current triage model uses:

```text
urgency_level: 1–5
priority_score: 0–100
```

The priority score is an operational scheduling representation.

It is not a diagnosis.

The triage policy engine applies predefined backend rules to structured clinical signals.

The LLM is not given arbitrary authority over queue ordering.

---

# Queue

Aurora uses a department-wide patient-centric queue.

The current MVP focuses on:

```text
General Medicine
```

Conceptually:

```text
Patient
   ↓
Department Queue
   ↓
Priority / Waiting-Time Policy
   ↓
Assignment Scheduler
   ↓
Doctor
```

Queue entries maintain information such as:

- session
- department
- status
- queue position
- urgency level
- priority score
- assigned doctor
- queued timestamp
- called timestamp
- completion timestamp

The doctor queue is a filtered view of the department queue.

The frontend does not become a second source of truth for ordering.

---

# Waiting Time

Waiting time is calculated from the queue entry's `queued_at` timestamp.

Aurora stores application timestamps as UTC.

The backend/database boundary uses UTC-aware datetime handling so that the same instant is represented consistently across:

```text
MongoDB
   ↓
FastAPI
   ↓
Frontend
   ↓
Browser
```

The doctor interface can update the elapsed waiting time live.

---

# Doctor Assignment

The current assignment workflow operates within General Medicine.

Assignment considers the current operational state of the department and eligible doctors.

The high-level flow is:

```text
Queue Entry
      ↓
Eligible Doctors
      ↓
Availability / Workload
      ↓
Assignment Scheduler
      ↓
Doctor Assignment
```

The patient does not need to know the internal scheduling calculation.

---

# Promotion and Reassignment

Aurora supports an operational promotion workflow.

A patient may become a promotion candidate when another eligible doctor could potentially provide earlier attention.

The flow is:

```text
Queue
  ↓
Promotion Candidate
  ↓
Promotion Request
  ↓
Admin / Reception
  ├── Approve
  ├── Deny
  └── No decision
           ↓
     Policy-driven timeout
```

The current workflow includes a short administrative decision window.

Promotion is an operational scheduling mechanism and does not replace clinical triage.

Reassignment is recorded separately from the original assignment.

---

# Real-Time Synchronization

Aurora uses Server-Sent Events (SSE) for live operational updates.

The backend exposes:

```text
GET /api/v1/events/stream?department_id=general-medicine
```

Current event types include:

```text
QUEUE_UPDATED
ASSIGNMENT_UPDATED
PROMOTION_UPDATED
```

The doctor and admin frontends use authenticated fetch-based SSE connections.

The frontend reconnects automatically when the stream is interrupted.

The current event bus is an in-process backend event bus.

This implementation is appropriate for the current single-process/demo architecture but does not provide durable event replay across multiple backend processes.

---

# Authentication and Authorization

There are two authenticated staff roles:

```text
DOCTOR
ADMIN
```

The patient kiosk does not use a normal application account.

Patient identity is established through the kiosk verification flow.

Staff authentication uses bearer-token-based application sessions.

Authorization is enforced by the backend.

Examples:

```text
DOCTOR
  ↓
Assigned patient case
Assigned department
Doctor queue

ADMIN
  ↓
Department operations
Queue monitoring
Promotion
Reassignment
```

Frontend visibility must never be treated as an authorization boundary.

---

# External Integrations

External healthcare-system integrations are isolated under:

```text
backend/integrations/
```

Current development uses mock implementations for:

```text
ABHA / Identity
FHIR
HIS / EMR
```

The objective is to keep external provider details outside the core domain.

Conceptually:

```text
Aurora Core
    ↓
Integration Interface
    ├── Identity / ABHA
    ├── FHIR
    └── HIS / EMR
```

The mock implementations allow the full workflow to be demonstrated without requiring production hospital integrations.

---

# Data Model

The main persistent entities include:

```text
Patient
Doctor
Department
ClinicalSession
ConversationTurn
ClinicalSignal
Document
DocumentExtraction
ClinicalSummary
TriageResult
QueueEntry
DoctorAssignment
PromotionRequest
```

A simplified relationship is:

```text
Patient
   │
   └── Clinical Session
          ├── Conversation Turns
          ├── Clinical Signals
          ├── Documents
          │      └── Document Extraction
          ├── Clinical Summary
          ├── Triage Result
          ├── Queue Entry
          └── Doctor Assignment
```

---

# Repository Structure

```text
Aurora/
│
├── backend/
│   ├── ai/
│   ├── api/
│   ├── auth/
│   ├── database/
│   ├── domain/
│   ├── events/
│   ├── integrations/
│   ├── models/
│   └── services/
│
├── patient-web/
│
├── doctor-web/
│
├── admin-web/
│
├── docs/
│   ├── architecture.md
│   ├── api-contracts.md
│   └── tech-stack.md
│
└── README.md
```

The directories represent responsibility boundaries and are allowed to evolve as implementation progresses.

---

# Local Development

## Backend

Create or activate a Python virtual environment and install:

```bash
pip install -r backend/requirements.txt
```

Configure:

```text
backend/.env
```

At minimum, the JWT secret must satisfy the backend's configured minimum length.

Start the backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

---

## Frontend Applications

Each frontend is independently runnable.

Patient:

```bash
cd patient-web
npm install
npm run dev
```

Doctor:

```bash
cd doctor-web
npm install
npm run dev
```

Admin:

```bash
cd admin-web
npm install
npm run dev
```

Each application proxies `/api` to the backend during local Vite development.

---

# Frontend Quality Checks

Each frontend currently provides:

```bash
npm run lint
npm run build
```

The production build uses TypeScript project compilation followed by Vite:

```bash
tsc -b && vite build
```

---

# Demo Development

The repository contains mock identity and healthcare integrations so the complete workflow can be demonstrated without production hospital infrastructure.

The current demonstration environment is intended to support:

- patient registration
- identity verification
- OTP verification
- consent
- AI interview
- document upload
- OCR/extraction
- triage
- queueing
- assignment
- promotion
- doctor review
- admin operations

---

# Branching Workflow

The repository uses a simple two-branch development model:

```text
main
 ↓
Stable / demo-ready code

dev
 ↓
Active development and testing
```

Development work should normally happen on `dev`.

Changes should be promoted to `main` only after the affected workflow has been tested.

---

# Current MVP Scope

## Included

- Patient kiosk
- Doctor workspace
- Admin/reception dashboard
- General Medicine queue
- Mock patient identity / ABHA verification
- OTP flow
- Consent
- English patient flow
- Hindi patient flow
- Text interview
- Voice interview
- Mobile microphone permission preflight
- Clinical information extraction
- Clinical signal extraction
- Red-flag detection
- OCR / document extraction
- Original document viewing
- Structured extraction review
- Conversation audit
- AI-generated clinical summary
- Doctor summary editing
- Doctor summary confirmation
- Triage
- Priority score
- Waiting-time handling
- Doctor assignment
- Promotion
- Reassignment
- Real-time SSE synchronization
- UTC-aware timestamp handling
- Mock FHIR integration
- Mock HIS integration

---

# Deferred / Future Scope

Planned future capabilities include:

- production ABHA / ABDM integration
- production FHIR integration
- production HIS / EMR integration
- broader Indian-language support
- improved multilingual voice workflows
- richer clinical interview coverage
- advanced document understanding
- handwritten-document assistance
- specialist routing
- biometric authentication
- analytics
- mobile-native applications
- production-grade distributed event infrastructure
- production security and compliance hardening

---

# Design Principle

Aurora is an assistant for clinical workflow.

```text
AI
 ↓
Understand
 ↓
Structure
 ↓
Surface
 ↓
Doctor
 ↓
Review
 ↓
Confirm
```

The system is designed to reduce repetitive information-gathering while keeping clinical responsibility with authorized healthcare professionals.

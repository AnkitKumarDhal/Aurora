# Aurora — System Architecture

Aurora is an OPD-deployed AI-assisted clinical intake platform designed to reduce the time doctors spend manually collecting and organizing patient history.

The primary patient interaction takes place through a dedicated hospital-managed kiosk running the patient web application.

Aurora consists of three web applications:

- Patient Web
- Doctor Web
- Admin / Reception Web

All three applications communicate with the Aurora backend.

---

## 1. High-Level Architecture

```text
                         AURORA
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    Patient Web       Doctor Web       Admin Web
      / Kiosk                              / Reception
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                      Backend API
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
       Domain             AI            Integrations
       Layer            Layer              Layer
          │                │                 │
          └────────────────┼─────────────────┘
                           │
                           ▼
                        Database
```

The backend is the central system of record.

The frontend applications must not directly access the database.

---

## 2. Patient Kiosk

The patient-facing application is designed primarily for deployment on a touchscreen kiosk located inside the hospital OPD.

The kiosk is a hospital-managed device. Patients do not need a conventional Aurora username/password account.

The kiosk provides:

- language selection
- patient identity verification
- consent
- voice-based interaction
- text/touch-based interaction
- AI-assisted clinical history taking
- document capture
- completion of the intake process

The kiosk is intended to be usable by elderly, low-literacy, first-time and non-technical patients with minimal assistance.

---

## 3. Patient Flow

The primary patient journey is:

```text
Language Selection
        ↓
Welcome / Instructions
        ↓
Patient Identity Verification
        ↓
Consent
        ↓
Interaction Mode
   ┌────┴────┐
   ↓         ↓
 Voice      Text / Touch
   └────┬────┘
        ↓
AI Clinical History Interview
        ↓
Clinical Signal / Red-Flag Detection
        ↓
Document Capture
        ↓
Document Processing
        ↓
Structured Clinical Summary
        ↓
Priority Calculation
        ↓
Department Queue
        ↓
Intake Complete
        ↓
Kiosk Reset
```

The patient does not need to know:

- their assigned doctor
- their queue position
- the doctor's availability
- the internal priority score
- whether the system promoted or reassigned them

After completing the intake, the patient waits for hospital staff to call them.

---

## 4. Patient Identity

Patient identity verification is separate from conventional application authentication.

The initial implementation uses a mock identity / ABHA verification flow.

The eventual system is intended to support ABHA-based identity and integration.

The patient does not create or use a conventional Aurora application account for the kiosk flow.

A clinical session is created after the patient has been successfully verified and has provided the required consent.

---

## 5. Consent

Consent occurs before clinical information is collected.

The consent flow should explain that Aurora will collect and process the health information and documents provided by the patient to prepare their clinical history for the hospital consultation.

The consent interface should support:

- clear, simple language
- audio explanation
- supported local languages
- explicit acceptance
- explicit refusal

The exact legal wording will be finalized separately.

The architecture must allow consent information to be associated with the clinical session.

---

## 6. Clinical Session

A clinical session represents one OPD intake visit.

The session is the central object connecting the patient's information collected during that visit.

Conceptually:

```text
Patient
   │
   └── Clinical Session
          │
          ├── Conversation
          ├── Clinical Signals
          ├── Documents
          ├── Document Extractions
          ├── Clinical Summary
          └── Queue Entry
```

A session should have an explicit lifecycle.

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

Exceptional states may include:

```text
CANCELLED
ABANDONED
ERROR
```

---

## 7. AI Boundary

All AI-related implementation belongs under:

```text
backend/ai/
```

This directory is owned by the AI implementation side of the project.

It may contain:

- LLM
- NLP
- OCR
- STT / ASR
- TTS
- clinical conversation processing
- information extraction
- clinical signal extraction
- red-flag signal detection
- AI-specific utilities
- model-specific adapters

The exact models, providers and libraries are intentionally not fixed by the core backend.

The AI layer communicates with the rest of the backend through defined interfaces and structured data.

---

## 8. AI and Triage Separation

The AI system should not directly control the queue.

The intended flow is:

```text
Patient Conversation
        ↓
AI / NLP
        ↓
Structured Clinical Signals
        ↓
Triage Policy Engine
        ↓
Clinical Urgency
        ↓
Priority Score
        ↓
Queue Scheduler
```

The AI is responsible for understanding and structuring information.

The backend triage policy engine is responsible for applying predefined operational rules to structured clinical signals.

The queue system is responsible for ordering, assignment and promotion.

This separation prevents an unconstrained LLM from directly determining arbitrary queue positions.

---

## 9. Triage Policy Engine

The triage policy engine belongs to the backend domain layer.

Its responsibility is to transform structured clinical signals into an operational urgency classification and priority score.

The initial model uses:

```text
urgency_level: 1–5
priority_score: 0–100
```

The exact names, thresholds and clinical rules will be finalized with appropriate clinical input.

The urgency level is intended to be human-readable.

The numeric priority score is intended for scheduling and queue computation.

The triage policy engine is not a diagnostic engine.

It does not make an autonomous diagnosis or prescribe treatment.

---

## 10. Queue Architecture

The department-wide patient queue is the authoritative queue.

Patients are queue entities.

Doctors are clinical resources assigned to queue entries.

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

A doctor's patient list is a filtered view of the department queue.

The doctor-specific view must not become a separate source of truth.

---

## 11. Queue Priority

Queue ordering considers both clinical urgency and operational waiting time.

The system maintains separate concepts for:

### Clinical urgency

How urgently the patient should receive clinical attention.

### Priority score

A numeric representation of the patient's clinical priority.

### Waiting time

How long the patient has been waiting.

### Effective queue priority

The value used by the scheduler when determining queue order.

Conceptually:

```text
Clinical Signals
      ↓
Clinical Urgency
      ↓
Priority Score
      ↓
Waiting-Time Aging
      ↓
Effective Queue Priority
```

Waiting-time aging may increase a patient's operational priority without changing their underlying clinical urgency classification.

This prevents routine patients from being indefinitely starved by continuously arriving higher-priority patients.

---

## 12. Doctor Assignment

The initial MVP focuses on General Medicine.

Patients enter the General Medicine department queue.

The assignment scheduler considers factors such as:

- doctor availability
- doctor workload
- department eligibility
- patient urgency
- queue position
- waiting time

Conceptually:

```text
Department Queue
       ↓
Eligible Doctors
       ↓
Availability / Workload
       ↓
Assignment Scheduler
       ↓
Doctor Assignment
```

Specialist routing is not part of the initial MVP.

The data model should remain extensible enough to support departments and specialties later.

---

## 13. Promotion and Reassignment

Promotion is an operational scheduling mechanism.

A promotion may occur when a patient can receive substantially earlier attention from another eligible doctor.

Example:

```text
Patient
   │
   ├── Current Doctor: Dr. A
   ├── Current Estimated Wait: 20 min
   │
   └── Alternative:
          Dr. B
          Eligible: Yes
          Estimated Wait: 6 min
```

The queue scheduler can generate a promotion candidate.

The initial operational workflow is:

```text
Queue Scheduler
       ↓
Promotion Candidate
       ↓
Admin / Reception Interface
       ↓
60-second Decision Window
       │
       ├── Allow
       │
       ├── Deny
       │
       └── Timeout
              ↓
        Automatic Resolution
```

The system must remain capable of operating without human intervention.

Administrative interaction acts as an override / approval mechanism rather than being required for normal queue operation.

Emergency or clinically critical cases must not be indefinitely blocked by administrative inactivity.

All assignment and promotion changes should be recorded.

---

## 14. Doctor Web Application

The doctor-facing application is an authenticated web application.

The doctor flow is:

```text
Doctor Authentication
        ↓
Doctor Identity
        ↓
Department
        ↓
Department Queue
        ↓
Assigned Patients
        ↓
Patient Case
        ↓
History + Documents + Summary
        ↓
Review / Edit
        ↓
Approve / Confirm
        ↓
Consultation
```

The doctor retains clinical control over the AI-generated summary.

Aurora does not autonomously diagnose or prescribe.

---

## 15. Doctor Queue UI

The doctor queue is presented as a responsive card-based interface.

Patients appear as individual cards rather than as a conventional text table.

Conceptually:

```text
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ SEVERITY ACCENT  │  │ SEVERITY ACCENT  │  │ SEVERITY ACCENT  │
│                  │  │                  │  │                  │
│ Patient          │  │ Patient          │  │ Patient          │
│ Age              │  │ Age              │  │ Age              │
│                  │  │                  │  │                  │
│ Brief summary    │  │ Brief summary    │  │ Brief summary    │
│                  │  │                  │  │                  │
│ Severity         │  │ Severity         │  │ Severity         │
│ Waiting time     │  │ Waiting time     │  │ Waiting time     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

The top accent visually indicates the patient's urgency.

The backend determines the ordering.

The frontend only renders the ordered queue it receives.

---

## 16. Admin / Reception Application

The admin interface is intentionally minimal.

It is an operational interface rather than a clinical dashboard.

It provides:

- read-only department-wide patient-doctor queue
- promotion requests
- allow / deny controls
- promotion timeout state

The admin does not need access to the full clinical case simply to perform queue operations.

Conceptually:

```text
Admin / Reception
        ↓
Department Queue
        ↓
Promotion Request
        ↓
Allow / Deny
        ↓
Automatic Timeout Resolution
```

---

## 17. Security and Access Control

The patient kiosk does not use conventional patient application login.

Doctors and administrators use authenticated application sessions.

Authorization is enforced by the backend.

The frontend must never be treated as the authority for access control.

A doctor must not be able to arbitrarily access unrelated patient records.

Access should be determined by backend authorization rules involving factors such as:

- authenticated user
- role
- department
- assignment
- permitted clinical access

The exact authentication mechanism can evolve independently of the clinical workflow.

---

## 18. Database

The database is the persistent source of application data.

Core entities include:

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
QueueEntry
DoctorAssignment
PromotionRequest
```

The exact schema may evolve during implementation.

The database should preserve the patient's clinical history and the relevant information generated during each clinical session.

---

## 19. Integration Boundary

External healthcare systems are isolated under:

```text
backend/integrations/
```

Initial development uses mock implementations.

Planned integrations include:

```text
ABHA
FHIR
HIS / EMR
```

Conceptually:

```text
Aurora Internal Record
        ↓
Integration Interface
        ↓
┌───────┼────────┐
↓       ↓        ↓
ABHA   FHIR     HIS
```

The core Aurora domain should not depend directly on provider-specific implementation details.

---

## 20. Initial Integration Strategy

The initial implementation will use mocks for:

- patient identity / ABHA verification
- FHIR exchange
- HIS communication

The rest of Aurora should behave as though these integrations are available through stable internal interfaces.

Real integrations can later replace the mock implementations without requiring a redesign of the patient, doctor or queue workflows.

---

## 21. General Medicine Scope

The initial clinical routing scope is General Medicine.

The MVP does not require AI to autonomously determine which medical specialty a patient should visit.

Future versions may support specialty-aware routing or recommendations.

A future system may allow the AI to suggest a potentially relevant specialty based on structured clinical information, while leaving the final decision to an authorized healthcare professional.

---

## 22. Responsibility Boundaries

### Patient Web

Responsible for:

- patient interaction
- accessibility
- language selection
- identity verification flow
- consent
- voice/text input
- document capture
- intake progress

### Doctor Web

Responsible for:

- doctor authentication
- queue visualization
- patient case visualization
- history review
- document review
- summary editing
- summary confirmation

### Admin Web

Responsible for:

- queue monitoring
- promotion requests
- promotion approval/denial

### Backend Domain

Responsible for:

- persistence
- clinical session lifecycle
- queue
- triage policy
- priority calculation
- doctor assignment
- promotion
- authorization
- application APIs

### AI Layer

Responsible for:

- LLM
- NLP
- STT / ASR
- TTS
- OCR
- clinical conversation processing
- information extraction
- clinical signal extraction
- AI-specific processing

### Integration Layer

Responsible for:

- ABHA
- FHIR
- HIS / EMR
- future external healthcare systems

---

## 23. Current MVP Scope

### In Scope

- Patient kiosk web application
- Doctor web application
- Admin / reception web application
- Patient identity verification mock
- Consent flow
- Clinical session management
- Patient records
- Persistent clinical history
- Document records
- Clinical summary records
- General Medicine queue
- Clinical urgency model
- Priority score
- Waiting-time aging
- Automatic doctor assignment
- Automatic promotion
- Administrative promotion override
- Backend API
- Database
- Mock ABHA integration
- Mock FHIR integration
- Mock HIS integration
- AI integration boundaries

### Deferred

- Production ABHA integration
- Production FHIR integration
- Production HIS / EMR integration
- Biometric authentication
- Specialist AI routing
- Mobile application
- Advanced analytics
- Production deployment/security certification

# Aurora

Aurora is an AI-assisted clinical intake platform designed for deployment in hospital outpatient departments (OPDs).

The system moves structured history-taking and medical document collection to the beginning of the patient's OPD journey, allowing the patient to complete much of the information-gathering process before seeing the doctor.

## Product Flow

```text
Patient
   ↓
OPD Kiosk
   ↓
Identity Verification
   ↓
Consent
   ↓
AI Clinical History
   ↓
Document Capture
   ↓
Structured Clinical Summary
   ↓
Priority Calculation
   ↓
Department Queue
   ↓
Doctor Assignment
   ↓
Doctor Review
   ↓
Consultation
```

The patient interacts with a dedicated touchscreen kiosk.

The doctor uses a separate authenticated web application.

Reception/admin staff use a lightweight operational web application for queue monitoring and promotion decisions.

---

## Applications

Aurora consists of three web applications and one backend.

```text
Aurora/
├── backend/
├── patient-web/
├── doctor-web/
└── admin-web/
```

### Patient Web

The patient application is designed for deployment on an OPD kiosk.

It provides:

- language selection
- identity verification
- consent
- voice interaction
- text/touch interaction
- clinical history intake
- document capture
- intake completion

The patient does not use a conventional Aurora username/password account.

### Doctor Web

The doctor application is an authenticated clinical workspace.

It provides:

- doctor authentication
- department queue
- patient cards
- assigned patient view
- clinical history
- medical documents
- AI-generated summary
- summary editing
- summary confirmation

### Admin Web

The admin/reception application is intentionally minimal.

It provides:

- read-only department-wide patient-doctor queue
- promotion requests
- promotion approval/denial
- promotion timeout information

It is an operational interface and does not need to expose the complete clinical case.

---

## Backend

The backend is the central application layer.

It is responsible for:

- APIs
- patient records
- clinical sessions
- database access
- queue management
- triage policy
- priority calculation
- doctor assignment
- promotion
- authorization
- external integration interfaces

The backend does not directly expose the database to frontend applications.

---

## AI Layer

AI-related functionality is isolated under:

```text
backend/ai/
```

This includes areas such as:

- LLM
- NLP
- OCR
- STT / ASR
- TTS
- clinical conversation processing
- information extraction
- clinical signal extraction
- red-flag detection

The specific AI models and providers are selected separately from the core backend.

The core application should communicate with AI components through defined interfaces rather than depending directly on a particular AI provider.

---

## Queue System

Aurora uses a department-wide patient queue.

Patients are the queue entities.

Doctors are resources assigned to queue entries.

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

The initial clinical scope is General Medicine.

The queue maintains:

- clinical urgency
- priority score
- waiting time
- effective queue priority
- assigned doctor
- queue status

The doctor application renders the queue as a responsive card-based interface.

The card's top accent indicates the patient's severity.

---

## Priority System

Aurora separates clinical urgency from operational scheduling.

```text
Patient Information
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

The initial model uses:

```text
urgency_level: 1–5
priority_score: 0–100
```

Waiting-time aging may influence operational queue order without changing the patient's underlying clinical urgency.

The AI does not directly determine arbitrary queue positions.

The backend triage policy engine applies predefined rules to structured clinical signals.

---

## Doctor Assignment

The initial MVP operates within General Medicine.

The assignment scheduler considers:

- department eligibility
- doctor availability
- doctor workload
- patient urgency
- queue position
- waiting time

The patient does not need to know which doctor they have been assigned to.

Hospital staff call the patient when the patient is ready to enter the consultation.

---

## Promotion

Aurora can identify situations where a patient may receive substantially earlier attention from another eligible doctor.

The system can create a promotion request.

```text
Queue Scheduler
      ↓
Promotion Candidate
      ↓
Admin / Reception
      ↓
Allow / Deny
      ↓
Automatic Resolution on Timeout
```

The administrative decision window is initially one minute.

The system remains capable of automatically resolving the request if no administrative action occurs.

Emergency or clinically critical cases must not be indefinitely blocked by administrative inactivity.

---

## Patient Session

A clinical session represents one OPD intake visit.

The session connects:

```text
Patient
   │
   └── Clinical Session
          ├── Conversation
          ├── Clinical Signals
          ├── Documents
          ├── Document Extractions
          ├── Clinical Summary
          └── Queue Entry
```

A session progresses through states such as:

```text
CREATED
IDENTIFYING
CONSENTED
HISTORY_IN_PROGRESS
DOCUMENT_PROCESSING
SUMMARY_READY
QUEUED
ASSIGNED
CALLED
IN_CONSULTATION
COMPLETED
```

Temporary kiosk state should be cleared after the intake session is completed.

---

## External Integrations

Initial development uses mock implementations for:

- ABHA
- FHIR
- HIS / EMR

The integration layer is located under:

```text
backend/integrations/
```

The core application communicates with these systems through internal interfaces.

The eventual goal is to replace the mock implementations with appropriate real integrations without restructuring the core Aurora workflow.

---

## Repository Structure

```text
Aurora/
│
├── backend/
│   ├── ai/
│   ├── api/
│   ├── database/
│   ├── domain/
│   ├── integrations/
│   └── models/
│
├── patient-web/
│
├── doctor-web/
│
├── admin-web/
│
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   └── tech-stack.md
│
└── README.md
```

The structure is expected to evolve as implementation progresses.

The directories represent responsibility boundaries rather than immutable architectural requirements.

---

## Development Scope

### Current MVP

- Patient kiosk web application
- Doctor web application
- Admin/reception web application
- Patient identity verification mock
- Consent
- Clinical session management
- Persistent patient records
- Clinical history
- Document records
- Clinical summaries
- General Medicine queue
- Priority system
- Doctor assignment
- Automatic promotion
- Administrative promotion override
- Backend API
- Database
- Mock ABHA integration
- Mock FHIR integration
- Mock HIS integration
- AI integration boundaries

### Future

- Real ABHA integration
- Real FHIR integration
- Real HIS / EMR integration
- Specialist routing recommendations
- Biometric authentication
- Advanced analytics
- Mobile application

---

## Development Order

The project is being rebuilt from the ground up.

The intended implementation order is:

```text
1. Backend Foundation
        ↓
2. Patient Intake
        ↓
3. Doctor Queue and Patient Case
        ↓
4. Priority / Triage
        ↓
5. Doctor Assignment
        ↓
6. Promotion
        ↓
7. Admin / Reception
        ↓
8. AI Integrations
        ↓
9. External Healthcare Integrations
```

The architecture may change as implementation reveals better solutions.

The product workflow and responsibility boundaries are the primary constraints; individual directories, files and implementation details may evolve accordingly.

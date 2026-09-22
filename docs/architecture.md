# Aurora — System Architecture

Aurora is organized as three independent user interfaces connected to a central backend.

```text
                                    ┌─────────────────┐
                                    │   Patient Web   │
                                    │     / Kiosk     │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  Doctor Web     │
                                    │ Clinical UI     │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   Admin Web     │
                                    │ Operations UI   │
                                    └────────┬────────┘
                                             │
                                             ▼
                              ┌─────────────────────────────┐
                              │       FastAPI Backend       │
                              │                             │
                              │ API • Auth • Services       │
                              │ Queue • Triage • Workflow   │
                              │ AI • Events • Integrations  │
                              └──────────────┬──────────────┘
                                             │
                                     ┌───────┴────────┐
                                     ▼                ▼
                             ┌─────────────┐   ┌─────────────┐
                             │   MongoDB   │   │ File Storage│
                             └─────────────┘   └─────────────┘
```

---

## 1. Frontend Applications

Aurora intentionally has three separate frontends because each serves a different user.

### Patient Web

Designed for kiosk use:

- simple interaction
- large controls
- touch input
- voice/text interaction
- multilingual flow

### Doctor Web

Designed for clinical review:

- queue
- patient case
- clinical summary
- documents
- OCR verification
- conversation audit
- consultation workflow

### Admin Web

Designed for operations:

- department queue
- doctor workload
- assignments
- promotion workflow

---

## 2. Backend

The backend is the system of record and contains the main application logic.

```text
backend/
├── api/            HTTP routes and schemas
├── auth/           authentication and authorization
├── domain/         core business entities
├── services/       application workflows
├── ai/             AI / extraction logic
├── events/         real-time events
├── integrations/   external system adapters
├── database/       repositories and DB access
└── models/         persistence models
```

The frontend never accesses the database directly.

---

## 3. Core Clinical Flow

```text
Patient
   ↓
Identity Verification
   ↓
Consent
   ↓
AI Clinical Interview
   ↓
Document Upload
   ↓
OCR / Extraction
   ↓
Clinical Signals
   ↓
Triage
   ↓
Clinical Summary
   ↓
Queue
   ↓
Doctor Assignment
   ↓
Doctor Review
   ↓
Consultation
```

---

## 4. Clinical Data Flow

The AI layer does not directly control the queue.

```text
Patient Conversation
        ↓
AI / Extraction
        ↓
Clinical Signals
        ↓
Triage Policy
        ↓
Urgency / Priority
        ↓
Queue Scheduler
        ↓
Doctor Assignment
```

This separates AI interpretation from deterministic workflow and scheduling logic.

---

## 5. Documents & Verification

Uploaded documents are preserved along with their extracted information.

```text
Original Document
       │
       ├── OCR / Extraction
       │       ├── Raw Text
       │       └── Structured Data
       │
       └── Doctor Verification
```

The doctor can compare:

```text
Original
   ↕
OCR
   ↕
Structured Extraction
```

This is particularly important for handwritten or poorly scanned documents.

---

## 6. Conversation Audit

Every clinical interview is associated with persisted conversation turns.

```text
Patient Answer
      ↓
AI Response
      ↓
Clinical Extraction
      ↓
Clinical Summary
```

The doctor can review the original patient/AI conversation to identify misunderstandings or extraction errors.

---

## 7. Queue Architecture

Aurora uses a department-wide patient queue.

```text
Patient
   ↓
Department Queue
   ↓
Priority + Waiting Time
   ↓
Assignment
   ↓
Doctor
```

The department queue is the source of truth.

Doctor and admin queues are views of the same underlying queue state.

---

## 8. Real-Time Updates

Aurora uses Server-Sent Events.

```text
Backend Mutation
      ↓
Event Bus
      ↓
SSE
      ↓
Doctor / Admin UI
```

Current events:

```text
QUEUE_UPDATED
ASSIGNMENT_UPDATED
PROMOTION_UPDATED
```

The current implementation uses an in-process event bus suitable for the MVP/demo architecture.

---

## 9. External Integrations

External healthcare systems are isolated behind integration boundaries.

```text
Aurora Backend
      ↓
Integration Layer
   ┌──┼────┐
   ↓  ↓    ↓
 ABHA FHIR HIS
```

The current implementation uses mocks for these integrations.

---

## 10. Key Architectural Principles

```text
Frontend
    → user interaction

Backend
    → application authority

Domain / Services
    → business workflow

AI
    → extraction and interpretation

Triage
    → policy

Queue
    → scheduling and assignment

Integrations
    → external systems

Database
    → persistent state
```

AI assists the workflow; it does not replace the backend's policy logic or the doctor's clinical judgment.

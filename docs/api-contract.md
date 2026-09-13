# Aurora — API Contract

**Base URL (dev):** `http://localhost:8000`
**Format:** All requests/responses are JSON unless noted. All timestamps are ISO 8601 UTC strings.
**Auth (MVP):** No token-based auth yet. Patient identity is carried via `patient_id` in the request body/path. Doctor-side endpoints are open in MVP (mock auth) — to be gated later.

---

## 0. Conventions

- All IDs (`patient_id`, `session_id`, `document_id`) are UUID v4 strings, generated server-side.
- All list endpoints return `{ "items": [...], "count": n }`.
- All error responses follow:
```json
  { "error": { "code": "string", "message": "human readable" } }
```
  with an appropriate HTTP status code (400, 404, 422, 500).
- Every endpoint below that mutates data returns the full updated resource, not just an ID, so clients don't need a follow-up GET.

---

## 1. Auth / Patient identity

### `POST /auth/register`
Creates a new patient record on first visit.

**Request**
```json
{
  "name": "string",
  "age": 34,
  "gender": "male | female | other",
  "phone": "string"
}
```

**Response `201`**
```json
{
  "patient_id": "uuid",
  "login_id": "string (8-char code, used for return visits)",
  "name": "string",
  "age": 34,
  "gender": "string",
  "phone": "string",
  "created_at": "datetime"
}
```

**Errors:** `422` invalid/missing fields.

---

### `POST /auth/login`
Logs in a returning patient using their `login_id` (generated at registration; printed on visit slip / shown in app).

**Request**
```json
{ "login_id": "string" }
```

**Response `200`** — same shape as register response.
**Errors:** `404` if `login_id` not found.

> **Open decision:** what the `login_id` actually is (self-generated 8-char code vs. phone number vs. hospital UHID). Needs to be locked by the team before OCR/return-visit logic can be finalized.

---

## 2. Sessions (the OPD visit / conversation)

### `POST /sessions`
Starts a new OPD visit session for a patient. Returns the AI's first question.

**Request**
```json
{ "patient_id": "uuid" }
```

**Response `201`**
```json
{
  "session_id": "uuid",
  "status": "in_progress",
  "first_question": {
    "role": "ai",
    "text": "What brings you in today?",
    "turn": 1
  }
}
```

---

### `GET /sessions/{session_id}`
Fetches full session state (used to resume/restore a conversation, e.g. on app relaunch).

**Response `200`**
```json
{
  "session_id": "uuid",
  "patient_id": "uuid",
  "status": "in_progress | summarized | approved",
  "red_flag": false,
  "conversation": [
    { "role": "ai", "text": "What brings you in today?", "turn": 1 },
    { "role": "patient", "text": "My chest hurts", "turn": 1, "input_mode": "voice" }
  ],
  "created_at": "datetime"
}
```
**Errors:** `404` unknown `session_id`.

---

### `POST /sessions/{session_id}/converse`
Core adaptive-questioning endpoint. Patient answers current question (voice-transcribed or typed text); server calls the LLM to decide the next question, and separately runs red-flag detection on the growing transcript.

**Request**
```json
{
  "text": "string (patient's answer, already transcribed if voice)",
  "input_mode": "text | voice"
}
```

**Response `200`**
```json
{
  "next_question": "string | null",
  "turn": 2,
  "red_flag": false,
  "red_flag_reason": "string | null",
  "status": "in_progress | ready_for_summary"
}
```
- `next_question: null` + `status: "ready_for_summary"` signals the AI has gathered enough to move to summary generation — client should call `GET /sessions/{id}/summary` next.
- `red_flag: true` should surface an urgent-attention UI state immediately in the mobile app AND bump priority in the doctor queue.

**Errors:** `404` unknown session, `409` if session already `summarized`/`approved`.

---

### `POST /sessions/{session_id}/skip`
Patient skips/doesn't know the answer to the current question. Still advances the conversation.

**Request**
```json
{ "reason": "dont_know | prefer_not_to_say | other" }
```

**Response `200`** — same shape as `/converse`.

---

## 3. Documents (photographed prescriptions / lab reports)

### `POST /sessions/{session_id}/documents`
Uploads a document image (multipart/form-data) for OCR + extraction. Async — returns immediately with a processing status; client polls `GET /documents/{id}`.

**Request:** `multipart/form-data`
- `file`: image (jpeg/png)
- `type`: `prescription | lab_report | discharge_summary`

**Response `202`**
```json
{
  "document_id": "uuid",
  "session_id": "uuid",
  "type": "prescription",
  "status": "processing",
  "uploaded_at": "datetime"
}
```

---

### `GET /documents/{document_id}`
Poll for OCR + extraction result.

**Response `200`**
```json
{
  "document_id": "uuid",
  "session_id": "uuid",
  "type": "prescription",
  "status": "processing | done | failed",
  "ocr_raw_text": "string | null",
  "extracted": {
    "diagnoses": ["string"],
    "medications": ["string"],
    "investigations": ["string"],
    "date": "string | null"
  },
  "uploaded_at": "datetime"
}
```
**Errors:** `404` unknown document.

---

## 4. Summary (evidence-linked case sheet)

### `GET /sessions/{session_id}/summary`
Generates (if not already done) or fetches the structured, evidence-linked case summary. This is the core output artifact of the product — every field must carry a `source` pointing back to the conversation turn(s) or document(s) it was derived from.

**Response `200`**
```json
{
  "session_id": "uuid",
  "chief_complaint": { "text": "string", "source": ["turn_1"] },
  "hpi": { "text": "string", "source": ["turn_1", "turn_2", "turn_3"] },
  "past_medical_history": { "text": "string", "source": ["doc_<id>"] },
  "drug_allergy_history": { "text": "string", "source": [] },
  "family_history": { "text": "string", "source": [] },
  "review_of_systems": { "text": "string", "source": [] },
  "red_flag": false,
  "status": "draft | approved",
  "doctor_edits": [
    { "field": "string", "old_text": "string", "new_text": "string", "edited_at": "datetime" }
  ]
}
```
**Errors:** `409` if session doesn't have enough conversation turns yet (`status` still `in_progress`).

---

## 5. Doctor-side (web dashboard)

### `GET /doctor/queue`
List of active sessions, sorted with red-flagged sessions first, then by wait time.

**Response `200`**
```json
{
  "items": [
    {
      "session_id": "uuid",
      "patient_name": "string",
      "patient_age": 34,
      "status": "in_progress | summarized | approved",
      "red_flag": false,
      "waiting_since": "datetime"
    }
  ],
  "count": 12
}
```

---

### `GET /doctor/patients/{session_id}`
Full case view for one patient: summary + all uploaded documents + raw conversation transcript, for doctor review.

**Response `200`**
```json
{
  "session_id": "uuid",
  "patient": { "patient_id": "uuid", "name": "string", "age": 34, "gender": "string" },
  "summary": { "...same shape as GET /sessions/{id}/summary..." },
  "documents": [{ "...same shape as GET /documents/{id}..." }],
  "conversation": [{ "role": "ai | patient", "text": "string", "turn": 1 }]
}
```

---

### `POST /doctor/patients/{session_id}/approve`
Doctor edits and/or approves the case sheet, finalizing it.

**Request**
```json
{
  "edits": [
    { "field": "chief_complaint", "new_text": "string" }
  ]
}
```

**Response `200`** — returns the finalized summary with `status: "approved"` and `doctor_edits` populated.

---

## 6. Status codes reference

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 202 | Accepted (async processing started) |
| 400 | Bad request |
| 404 | Resource not found |
| 409 | Conflict (invalid state transition) |
| 422 | Validation error (bad request body) |
| 500 | Server error |

## 7. Open decisions (flag these to the team explicitly)

1. **`login_id` scheme** — self-generated code vs. phone vs. hospital ID.
2. **LLM choice** — hosted Claude/LLM API vs. local Gemma small model (cost/latency/offline trade-off).
3. **Red-flag detection** — rule-based keyword matching vs. LLM-judged, and what the actual red-flag criteria list is (needs clinical input, not just engineering).
4. **Polling vs. websockets** for document OCR status — polling is simpler and is the current contract; fine for MVP.

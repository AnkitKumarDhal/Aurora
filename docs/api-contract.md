POST   /auth/register          → create new patient, returns patient_id + login_id
POST   /auth/login              → login existing patient via login_id
POST   /sessions                → start a new OPD visit session, returns session_id
GET    /sessions/{id}           → get session state

POST   /sessions/{id}/converse  → send patient's answer (text or transcribed voice),
                                    returns next adaptive question + red_flag status
POST   /sessions/{id}/skip      → mark current question as "I don't know" / skipped

POST   /sessions/{id}/documents → upload a document (image), returns OCR job status
GET    /documents/{id}          → get OCR + extraction result for a document

GET    /sessions/{id}/summary   → generate/fetch structured case summary
                                    (evidence-linked: each field has source refs)

GET    /doctor/queue            → list of active sessions, sorted by priority/red-flag
GET    /doctor/patients/{id}    → full patient view: summary + docs + conversation
POST   /doctor/patients/{id}/approve → doctor edits + approves the case sheet

```json
// Patient
{
  "patient_id": "string",
  "login_id": "string",       // TBD which ID scheme
  "name": "string",
  "age": "number",
  "gender": "string",
  "phone": "string",
  "created_at": "datetime"
}

// Session
{
  "session_id": "string",
  "patient_id": "string",
  "status": "in_progress | summarized | approved",
  "red_flag": false,
  "conversation": [
    {"role": "ai", "text": "...", "turn": 1},
    {"role": "patient", "text": "...", "turn": 1, "input_mode": "voice|text|skip"}
  ],
  "created_at": "datetime"
}

// Document
{
  "document_id": "string",
  "session_id": "string",
  "type": "prescription|lab_report|discharge_summary",
  "ocr_raw_text": "string",
  "extracted": {
    "diagnoses": [],
    "medications": [],
    "investigations": [],
    "date": "string"
  },
  "uploaded_at": "datetime"
}

// Summary (evidence-linked)
{
  "session_id": "string",
  "chief_complaint": {"text": "...", "source": ["turn_1"]},
  "hpi": {"text": "...", "source": ["turn_1", "turn_2", "turn_3"]},
  "past_medical_history": {"text": "...", "source": ["doc_id_1"]},
  "drug_allergy_history": {"text": "...", "source": []},
  "family_history": {"text": "...", "source": []},
  "review_of_systems": {"text": "...", "source": []},
  "red_flag": false,
  "status": "draft|approved",
  "doctor_edits": []
}
```

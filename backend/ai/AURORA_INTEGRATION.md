# MediKiosk → Aurora Clinical Intelligence Integration

## Purpose

This package provides the clinical-intelligence boundary that plugs into Aurora.

Aurora remains responsible for:

- patient/session persistence
- conversation persistence
- document persistence
- clinical signal persistence
- clinical summary persistence
- triage scoring
- queue ordering
- promotion
- doctor assignment
- physician confirmation

MediKiosk provides:

- adaptive clinical questioning
- deterministic clinical extraction
- optional AI semantic extraction
- red-flag detection
- AYUSH assessment
- evidence/provenance
- contradiction preservation
- document-derived clinical facts
- cross-source discrepancies
- clinical timeline
- physician-summary generation

## Public interface

The only integration class Aurora needs to know about is:

```python
from aurora_integration import AuroraClinicalAdapter

adapter = AuroraClinicalAdapter()
```

### 1. Process one patient turn

```python
result = adapter.process_turn(
    session_id=session_id,
    patient_text=patient_message,
    previous_patient_turns=aurora_patient_turns,
    language=language,
)
```

`previous_patient_turns` are the patient conversation turns already persisted by Aurora. Do not include the new `patient_text` in that list.

Returned fields include:

```text
session_id
assistant_response
next_question
field
completed
history
red_flags
triage_required
physician_review_required
contradictions
clinical_evidence
signals
```

### 2. Extract Aurora ClinicalSignals

```python
result = adapter.extract_signals(
    session_id=session_id,
    patient_turns=aurora_patient_turns,
    document_summaries=document_outputs,
)
```

Each signal follows Aurora's existing shape:

```text
signal_id
session_id
signal_type
name
value
confidence
source
```

Signal IDs are deterministic for the same session/name/value/source combination, so rebuilding the clinical state does not create random IDs.

The adapter does not calculate Aurora queue priority or assign a doctor.

### 3. Generate the physician summary

```python
result = adapter.generate_summary(
    session_id=session_id,
    patient_turns=aurora_patient_turns,
    document_summaries=document_outputs,
    generate_ai_draft=False,
)
```

`result["aurora_summary"]` matches Aurora's current clinical-summary contract:

```text
session_id
chief_complaint
history_of_present_illness
past_medical_history
medications
allergies
relevant_documents
clinical_signals
generated_at
```

The complete MediKiosk physician summary remains available under:

```text
result["physician_summary"]
```

This preserves the richer evidence/timeline/discrepancy information without forcing those concepts into Aurora's existing summary model.

### 4. Triage hand-off

The adapter returns:

```text
result["triage_inputs"]
```

These use signal names understood by Aurora's existing TriageEngine, such as:

```text
severe_pain
moderate_pain
persistent_symptoms
loss_of_consciousness
severe_breathing_difficulty
stroke_symptoms
severe_chest_pain
active_severe_bleeding
suicidal_intent
```

MediKiosk does not calculate Aurora's `urgency_level` or `priority_score`.
Aurora's own TriageService/TriageEngine remains authoritative for those decisions.

## Stateless design

There is intentionally no:

```python
sessions = {}
```

and no global patient state.

The adapter reconstructs a fresh clinical engine from Aurora-persisted patient turns for each call.

Aurora remains the source of truth for the clinical session and conversation.

## Conversation flow

```text
Aurora creates session
        ↓
Aurora stores patient turn
        ↓
Aurora passes session_id + previous patient turns to MediKiosk
        ↓
MediKiosk extracts clinical facts
        ↓
MediKiosk returns next question + signals + evidence
        ↓
Aurora persists ClinicalSignals
        ↓
Patient continues
        ↓
Aurora requests final summary
        ↓
MediKiosk returns physician summary + signals + triage inputs
        ↓
Aurora persists ClinicalSummary
        ↓
Aurora TriageService evaluates ClinicalSignals
        ↓
Aurora Queue / workflow remains authoritative
        ↓
Doctor reviews and confirms summary
```

## Important integration boundary

Do not add another session system, queue, triage system, promotion system, or assignment system around this adapter.

The adapter is intentionally a clinical-intelligence boundary only.

## Optional modules

OCR/document extraction and voice transcription remain optional. The core patient conversation path does not require them.

When Aurora already owns audio transcription, the resulting transcript can be passed to `process_turn()` as `patient_text`.

When Aurora already owns document upload/extraction persistence, pass the resulting structured extraction into `document_summaries`.

## AI configuration

Core clinical operation does not require an external AI provider.

AI is optional and should remain explicitly configurable through the MediKiosk AI settings.

Recommended default for deterministic integration testing:

```text
MEDIKIOSK_AI_ENABLED=0
MEDIKIOSK_AI_PROVIDER=off
```

## Validation

Run:

```powershell
python test_aurora_integration.py
```

The contract test verifies:

- session reconstruction is stateless
- patient turns produce a next question
- Aurora ClinicalSignal-shaped payloads are valid
- Aurora ClinicalSummary-shaped output is valid
- Aurora triage signal names are emitted without calculating queue priority
- signal IDs are deterministic across repeated reconstruction

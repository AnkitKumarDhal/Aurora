# MediKiosk Clinical Audit Fixes

This handoff note covers the clinical-intelligence changes made during the full-project audit. Frontend, authentication, database, queue ownership, persistence, and other backend-owned infrastructure were not modified.

## Fixed

- Added the real initial patient-facing question to `ClinicalSession.get_next_question()` so `/clinical/start` no longer reports a new session as complete.
- Made the core onset question part of the deterministic queue. When onset is not already explicit in the chief complaint, the engine asks for it.
- Expanded the general clinical queue to include:
  - previous medical conditions
  - surgical history
  - current medications
  - allergies
  - family history
  - diet
  - sleep
  - smoking/tobacco
  - alcohol
  - physical activity
  - review of systems: general, respiratory, cardiovascular, gastrointestinal, neurological
- Canonicalized all 11 required AYUSH/Dashavidha fields in `clinical_schema.py`, while retaining the legacy `dashavidha` field for compatibility.
- Added a voice-to-clinical bridge: `ClinicalSession.process_audio_file(...)` uses the existing ASR layer and then routes the transcript through the same clinical logic as typed responses.
- Made the legacy `clinical_engine.py` safe to import by removing import-time interactive execution. The production engine remains `ClinicalSession`.
- Added source-aware laboratory abnormality screening. A result is classified only when the uploaded report supplies a reference range or an explicit abnormal flag. No normal range is invented.
- Added a conservative, explicitly limited medication-interaction screen and integrated it into the physician summary. A clean result means only that no supported built-in rule matched; it is not a complete interaction database.
- Added medication-interaction and laboratory-abnormality sections to physician-facing output.
- Added compatibility for the older `AI_ENABLED` / `AI_PROVIDER` environment variable names while retaining the `MEDIKIOSK_*` names.

## Safety boundary

The clinical engine continues to preserve raw patient statements, keep evidence provenance, preserve contradictions, and route clinically important discrepancies/alerts to physician review. The laboratory layer does not diagnose disease. The medication interaction layer is intentionally limited and does not replace pharmacist/physician review.

## Validation performed

The following key clinical tests passed after the fixes:

- AYUSH schema
- clinical evidence ledger
- red flags
- clinical edge cases
- clinical timeline
- cross-source discrepancy detection
- clinical start prompt
- voice-to-clinical bridge
- complaint routing
- contradiction preservation
- medication interaction screening
- laboratory abnormality screening
- laboratory extraction
- physician summary
- document-to-clinical bridge
- discharge extraction
- document pipeline
- full patient journey
- full question queue coverage

The full patient journey was also executed with AI disabled and reached `STATUS: PASS`.

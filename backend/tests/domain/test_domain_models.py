from backend.domain.clinical_signal import ClinicalSignal
from backend.domain.clinical_summary import ClinicalSummary
from backend.domain.enums import ClinicalSignalType, SummaryStatus
from backend.domain.patient import Patient


def test_patient_list_like_fields_are_independent():
    first = ClinicalSummary(
        summary_id="summary-001",
        session_id="session-001",
    )
    second = ClinicalSummary(
        summary_id="summary-002",
        session_id="session-002",
    )

    first.medications.append("Medication A")

    assert first.medications == ["Medication A"]
    assert second.medications == []


def test_doctor_and_patient_timestamped_models_have_timestamps():
    patient = Patient(
        patient_id="patient-001",
        display_name="Test Patient",
    )

    assert patient.created_at is not None
    assert patient.updated_at is not None


def test_clinical_signal_accepts_confidence_bounds():
    signal = ClinicalSignal(
        signal_id="signal-001",
        session_id="session-001",
        signal_type=ClinicalSignalType.SYMPTOM,
        name="fever",
        value=True,
        confidence=0.95,
    )

    assert signal.confidence == 0.95


def test_summary_starts_in_generating_state():
    summary = ClinicalSummary(
        summary_id="summary-001",
        session_id="session-001",
    )

    assert summary.status == SummaryStatus.GENERATING
    assert summary.confirmed_by is None
    assert summary.confirmed_at is None

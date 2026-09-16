from backend.domain.enums import UrgencyLevel
from backend.services.triage_engine import TriageEngine


def test_critical_red_flag_gets_level_5():
    engine = TriageEngine()

    result = engine.assess([
        {"name": "severe_chest_pain", "value": True},
    ])

    assert result.urgency_level == UrgencyLevel.LEVEL_5
    assert result.priority_score == 100
    assert result.red_flags_present is True


def test_multiple_critical_flags_get_level_5():
    engine = TriageEngine()

    result = engine.assess([
        {"name": "severe_breathing_difficulty", "value": True},
        {"name": "loss_of_consciousness", "value": True},
    ])

    assert result.urgency_level == UrgencyLevel.LEVEL_5
    assert result.priority_score == 100
    assert result.red_flags_present is True


def test_severe_pain_gets_level_4():
    engine = TriageEngine()

    result = engine.assess([
        {"name": "severe_pain", "value": True},
    ])

    assert result.urgency_level == UrgencyLevel.LEVEL_4
    assert result.priority_score == 75
    assert result.red_flags_present is False


def test_moderate_pain_gets_level_3():
    engine = TriageEngine()

    result = engine.assess([
        {"name": "moderate_pain", "value": True},
    ])

    assert result.urgency_level == UrgencyLevel.LEVEL_3
    assert result.priority_score == 55
    assert result.red_flags_present is False


def test_persistent_symptoms_get_level_2():
    engine = TriageEngine()

    result = engine.assess([
        {"name": "persistent_symptoms", "value": True},
    ])

    assert result.urgency_level == UrgencyLevel.LEVEL_2
    assert result.priority_score == 35
    assert result.red_flags_present is False


def test_no_urgent_signal_gets_level_1():
    engine = TriageEngine()

    result = engine.assess([])

    assert result.urgency_level == UrgencyLevel.LEVEL_1
    assert result.priority_score == 20
    assert result.red_flags_present is False


def test_elderly_patient_increases_priority():
    engine = TriageEngine()

    result = engine.assess([
        {"name": "elderly_patient", "value": True},
    ])

    assert result.urgency_level == UrgencyLevel.LEVEL_1
    assert result.priority_score == 25


def test_pregnancy_increases_priority():
    engine = TriageEngine()

    result = engine.assess([
        {"name": "pregnancy", "value": True},
    ])

    assert result.urgency_level == UrgencyLevel.LEVEL_1
    assert result.priority_score == 25


def test_priority_is_capped_below_critical():
    engine = TriageEngine()

    result = engine.assess([
        {"name": "severe_pain", "value": True},
        {"name": "elderly_patient", "value": True},
        {"name": "pregnancy", "value": True},
    ])

    assert result.urgency_level == UrgencyLevel.LEVEL_4
    assert result.priority_score == 85
    assert result.priority_score < 100

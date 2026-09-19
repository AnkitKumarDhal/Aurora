from backend.ai.aurora_integration import AuroraClinicalAdapter


def _patient_turns() -> list[dict]:
    return [
        {
            "speaker": "patient",
            "content": "I have chest pain for three days.",
            "index": 0,
        },
        {
            "speaker": "patient",
            "content": "It is mostly on the right side of my chest.",
            "index": 1,
        },
        {
            "speaker": "patient",
            "content": "It feels like pressure.",
            "index": 2,
        },
        {
            "speaker": "patient",
            "content": "It spreads to my left arm.",
            "index": 3,
        },
        {
            "speaker": "patient",
            "content": "I am sweating.",
            "index": 4,
        },
        {
            "speaker": "patient",
            "content": "It is continuous.",
            "index": 5,
        },
        {
            "speaker": "patient",
            "content": "Running makes it worse.",
            "index": 6,
        },
        {
            "speaker": "patient",
            "content": "Rest makes it better.",
            "index": 7,
        },
        {
            "speaker": "patient",
            "content": "7.",
            "index": 8,
        },
    ]


def main() -> None:
    adapter = AuroraClinicalAdapter()

    first = adapter.process_turn(
        session_id="sess_demo",
        patient_text="I have chest pain for three days.",
        previous_patient_turns=[],
    )

    assert first["session_id"] == "sess_demo"
    assert first["field"] == "chief_complaint"
    assert isinstance(first["next_question"], str)
    assert first["next_question"].strip()
    assert isinstance(first["signals"], list)

    turns = _patient_turns()

    extracted = adapter.extract_signals(
        session_id="sess_demo",
        patient_turns=turns,
    )

    assert extracted["session_id"] == "sess_demo"
    assert extracted["signals"]

    assert any(
        signal["name"] == "severity"
        and signal["value"] == 7
        for signal in extracted["signals"]
    )

    assert any(
        signal["name"] == "severe_pain"
        and signal["value"] is True
        for signal in extracted["signals"]
    )

    assert any(
        item["name"] == "persistent_symptoms"
        for item in extracted["triage_inputs"]
    )

    assert any(
        item["name"] == "severe_chest_pain"
        and item["value"] is True
        for item in extracted["triage_inputs"]
    )

    summary = adapter.generate_summary(
        session_id="sess_demo",
        patient_turns=turns,
        document_summaries=[],
        generate_ai_draft=False,
    )

    aurora_summary = summary["aurora_summary"]

    expected_keys = {
        "session_id",
        "chief_complaint",
        "history_of_present_illness",
        "past_medical_history",
        "medications",
        "allergies",
        "relevant_documents",
        "clinical_signals",
        "generated_at",
    }

    assert expected_keys.issubset(
        aurora_summary.keys()
    )

    for key in (
        "past_medical_history",
        "medications",
        "allergies",
        "relevant_documents",
        "clinical_signals",
    ):
        assert isinstance(
            aurora_summary[key],
            list,
        )

    # Statelessness check: a fresh adapter produces the same signal IDs
    # from the same persisted Aurora turns.
    again = AuroraClinicalAdapter().extract_signals(
        session_id="sess_demo",
        patient_turns=turns,
    )

    assert [
        signal["signal_id"]
        for signal in extracted["signals"]
    ] == [
        signal["signal_id"]
        for signal in again["signals"]
    ]

    print("Aurora integration contract: PASS")
    print("Stateless session reconstruction: PASS")
    print("ClinicalSignal-compatible payloads: PASS")
    print("ClinicalSummary-compatible payload: PASS")
    print("Aurora triage hand-off: PASS")
    print("STATUS: PASS")


if __name__ == "__main__":
    main()

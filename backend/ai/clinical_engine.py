"""
Compatibility entry point for the legacy clinical engine.

The production clinical logic now lives in ClinicalSession. This module keeps
an optional CLI wrapper for older demos while avoiding import-time input() or
infinite loops.
"""

from .clinical_service import ClinicalSession


def run_interactive() -> None:
    session = ClinicalSession()

    print("\nMediKiosk:")
    print(session.get_next_question())

    first_response = input("Patient: ").strip()
    if not first_response:
        print("Please enter a response.")
        return

    result = session.process_response(first_response)

    while not session.completed:
        question = result.get("next_question") or session.get_next_question()
        if not question:
            break

        print("\nMediKiosk:")
        print(question)

        response = input("Patient: ").strip()
        if not response:
            print("Please enter a response.")
            continue

        result = session.process_response(response)

    print("\n========== PATIENT HISTORY ==========")
    for section, value in session.patient_history.items():
        print(f"{section}: {value}")

    print("\n========== TRIAGE ==========")
    print("Required:", session.triage_required)
    print("Red flags:", session.red_flags)


if __name__ == "__main__":
    run_interactive()

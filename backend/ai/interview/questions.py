from __future__ import annotations


QUESTIONS: dict[str, str] = {
    "chief_complaint": (
        "What is the main problem you are having today?"
    ),
    "onset": (
        "When did this problem start?"
    ),
    "site": (
        "Where exactly do you feel it?"
    ),
    "severity": (
        "How severe is it on a scale of 0 to 10?"
    ),
    "character": (
        "What does it feel like — for example, pressure, burning, "
        "throbbing, stabbing, or something else?"
    ),
    "timing": (
        "Is it constant, or does it come and go?"
    ),
    "aggravating_factors": (
        "What makes it worse?"
    ),
    "relieving_factors": (
        "What makes it better?"
    ),
    "radiation": (
        "Does the discomfort spread anywhere else?"
    ),
    "associated_symptoms": (
        "What other symptoms have you noticed with it?"
    ),
    "breathing_difficulty": (
        "Have you had any difficulty breathing or shortness of breath?"
    ),
    "nausea_vomiting": (
        "Have you had nausea or vomiting?"
    ),
    "vision_or_neuro": (
        "Have you had any vision changes, weakness, numbness, "
        "confusion, or other unusual neurological symptoms?"
    ),
    "cough": (
        "Have you had a cough?"
    ),
    "wheeze": (
        "Have you noticed wheezing or a whistling sound when breathing?"
    ),
    "location": (
        "Where in your abdomen or digestive system is the problem?"
    ),
    "bowel_changes": (
        "Have you noticed any change in your bowel movements?"
    ),
    "appearance": (
        "What does the affected skin area look like?"
    ),
    "itch_or_pain": (
        "Is the area itchy, painful, or both?"
    ),
    "spread": (
        "Has the affected area spread or changed size?"
    ),
    "urinary_frequency": (
        "Have you been urinating more or less often than usual?"
    ),
    "urinary_burning": (
        "Do you have burning or pain while urinating?"
    ),
    "urinary_blood": (
        "Have you noticed any blood in your urine?"
    ),
    "fever": (
        "Have you had a fever?"
    ),
    "fatigue": (
        "Have you felt unusually tired?"
    ),
    "weight_change": (
        "Have you had any unexpected weight change?"
    ),
}


def question_for(field: str) -> str:
    return QUESTIONS.get(
        field,
        "Is there anything else important about this symptom that you think the doctor should know?",
    )

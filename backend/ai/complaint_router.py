# ---------------------------------------------------------
# COMPLAINT ROUTER
# ---------------------------------------------------------
#
# Determines which clinical complaint categories are
# relevant based on the patient's chief complaint.
#
# IMPORTANT:
# This is NOT diagnosis.
# It only selects relevant question groups.
# ---------------------------------------------------------


COMPLAINT_KEYWORDS = {

    # -----------------------------------------------------
    # PAIN
    # -----------------------------------------------------

    "pain": [
        "pain",
        "ache",
        "aching",
        "hurt",
        "hurting",
        "discomfort"
    ],


    # -----------------------------------------------------
    # RESPIRATORY
    # -----------------------------------------------------

    "respiratory": [
        "cough",
        "breathing",
        "breathlessness",
        "breathless",
        "shortness of breath",
        "wheezing",
        "phlegm",
        "sputum"
    ],


    # -----------------------------------------------------
    # GASTROINTESTINAL
    # -----------------------------------------------------

    "gastrointestinal": [
        "stomach",
        "abdomen",
        "abdominal",
        "vomiting",
        "vomit",
        "nausea",
        "diarrhea",
        "diarrhoea",
        "constipation",
        "acidity",
        "indigestion",
        "heartburn"
    ],


    # -----------------------------------------------------
    # NEUROLOGICAL
    # -----------------------------------------------------

    "neurological": [
        "headache",
        "dizziness",
        "vertigo",
        "numbness",
        "weakness",
        "seizure",
        "tremor",
        "fainting",
        "fainted",
        "migraine"
    ],


    # -----------------------------------------------------
    # SKIN
    # -----------------------------------------------------

    "skin": [
        "rash",
        "itching",
        "itchy",
        "skin",
        "lesion"
    ],


    # -----------------------------------------------------
    # URINARY
    # -----------------------------------------------------

    "urinary": [
        "urine",
        "urination",
        "urinating",
        "burning urine",
        "blood in urine",
        "frequent urination",
        "kidney"
    ],


    # -----------------------------------------------------
    # GENERAL
    # -----------------------------------------------------

    "general": [
        "fever",
        "fatigue",
        "tired",
        "weakness",
        "weight loss",
        "weight gain",
        "loss of appetite",
        "appetite"
    ]
}


# ---------------------------------------------------------
# TERMS THAT SHOULD NOT ALSO TRIGGER GENERIC PAIN
# ---------------------------------------------------------

PAIN_EXCLUSIONS = [
    "headache",
    "migraine"
]


def classify_complaint(complaint):
    """
    Return complaint categories relevant to the
    patient's stated complaint.

    This function does NOT diagnose.

    It only determines which question groups should
    be considered for the clinical history interview.
    """

    if not complaint:

        return ["general"]


    text = complaint.lower().strip()

    categories = []


    # -----------------------------------------------------
    # DETERMINE WHETHER GENERIC PAIN SHOULD BE INCLUDED
    # -----------------------------------------------------

    generic_pain_allowed = True

    for excluded_term in PAIN_EXCLUSIONS:

        if excluded_term in text:

            generic_pain_allowed = False

            break


    # -----------------------------------------------------
    # MATCH CATEGORIES
    # -----------------------------------------------------

    for category, keywords in COMPLAINT_KEYWORDS.items():

        # Skip generic pain when the complaint is
        # specifically a headache/migraine.

        if (
            category == "pain"
            and not generic_pain_allowed
        ):

            continue


        for keyword in keywords:

            if keyword in text:

                if category not in categories:

                    categories.append(category)

                break


    # -----------------------------------------------------
    # EVERY PATIENT GETS GENERAL HISTORY
    # -----------------------------------------------------

    if "general" not in categories:

        categories.append("general")


    return categories
# =========================================================
# MEDIKIOSK CLINICAL QUESTION SCHEMA
# =========================================================
#
# The schema defines:
#
# 1. Core history
# 2. Complaint-specific history
# 3. General medical history
# 4. Review of systems
# 5. AYUSH history
#
# IMPORTANT:
#
# Each question has a specific "field".
#
# The clinical service uses that field to determine what
# information should be extracted from the patient's answer.
#
# Example:
#
# Question:
# "How severe is the pain?"
#
# Field:
# "severity"
#
# Patient:
# "I would say seven out of ten."
#
# Structured:
# severity = 7
#
# Raw response is ALSO preserved separately.
# =========================================================


# =========================================================
# CORE QUESTIONS
# =========================================================

CORE_QUESTIONS = [

    {
        "section": "history_of_present_illness",
        "field": "onset",
        "question": "When did the problem start?"
    }

]


# =========================================================
# PAIN / SOCRATES
# =========================================================

PAIN_QUESTIONS = [

    # S - SITE
    {
        "section": "history_of_present_illness",
        "field": "site",
        "question": "Where exactly do you feel the pain or discomfort?"
    },

    # C - CHARACTER
    {
        "section": "history_of_present_illness",
        "field": "character",
        "question": "How would you describe the pain or discomfort?"
    },

    # R - RADIATION
    {
        "section": "history_of_present_illness",
        "field": "radiation",
        "question": "Does the pain spread anywhere else?"
    },

    # A - ASSOCIATED SYMPTOMS
    {
        "section": "history_of_present_illness",
        "field": "associated_symptoms",
        "question": "Have you noticed any other symptoms along with the pain?"
    },

    # T - TIMING
    {
        "section": "history_of_present_illness",
        "field": "timing",
        "question": "Does the pain come and go, or is it continuous?"
    },

    # E - EXACERBATING FACTORS
    {
        "section": "history_of_present_illness",
        "field": "aggravating_factors",
        "question": "What makes the pain worse?"
    },

    # R - RELIEVING FACTORS
    {
        "section": "history_of_present_illness",
        "field": "relieving_factors",
        "question": "What makes the pain better?"
    },

    # S - SEVERITY
    {
        "section": "history_of_present_illness",
        "field": "severity",
        "question": "How severe is the pain on a scale of 0 to 10?"
    }

]


# =========================================================
# RESPIRATORY QUESTIONS
# =========================================================

RESPIRATORY_QUESTIONS = [

    {
        "section": "respiratory_history",
        "field": "breathing_difficulty",
        "question": "Are you having difficulty breathing or shortness of breath?"
    },

    {
        "section": "respiratory_history",
        "field": "cough",
        "question": "Do you have a cough?"
    },

    {
        "section": "respiratory_history",
        "field": "sputum",
        "question": "Are you bringing up any phlegm or sputum?"
    },

    {
        "section": "respiratory_history",
        "field": "wheezing",
        "question": "Have you noticed any wheezing or noisy breathing?"
    },

    {
        "section": "respiratory_history",
        "field": "respiratory_triggers",
        "question": "Does anything make your breathing problem or cough worse or better?"
    }

]


# =========================================================
# GASTROINTESTINAL QUESTIONS
# =========================================================

GASTROINTESTINAL_QUESTIONS = [

    {
        "section": "gastrointestinal_history",
        "field": "gi_location",
        "question": "Where exactly do you feel the stomach or abdominal problem?"
    },

    {
        "section": "gastrointestinal_history",
        "field": "nausea_vomiting",
        "question": "Have you experienced nausea or vomiting?"
    },

    {
        "section": "gastrointestinal_history",
        "field": "bowel_changes",
        "question": "Have you noticed any changes in your bowel movements?"
    },

    {
        "section": "gastrointestinal_history",
        "field": "appetite",
        "question": "How has your appetite been recently?"
    },

    {
        "section": "gastrointestinal_history",
        "field": "food_relation",
        "question": "Does the problem seem related to eating or any particular food?"
    }

]


# =========================================================
# NEUROLOGICAL QUESTIONS
# =========================================================

NEUROLOGICAL_QUESTIONS = [

    {
        "section": "neurological_history",
        "field": "neuro_location",
        "question": "Where do you feel the neurological symptom or discomfort?"
    },

    {
        "section": "neurological_history",
        "field": "dizziness",
        "question": "Have you experienced dizziness or a spinning sensation?"
    },

    {
        "section": "neurological_history",
        "field": "weakness",
        "question": "Have you experienced any weakness or difficulty moving?"
    },

    {
        "section": "neurological_history",
        "field": "numbness",
        "question": "Have you experienced any numbness or tingling?"
    },

    {
        "section": "neurological_history",
        "field": "vision",
        "question": "Have you experienced any changes in your vision?"
    },

    {
        "section": "neurological_history",
        "field": "headache_features",
        "question": "If you have a headache, what does it feel like and when does it occur?"
    }

]


# =========================================================
# SKIN QUESTIONS
# =========================================================

SKIN_QUESTIONS = [

    {
        "section": "skin_history",
        "field": "skin_location",
        "question": "Where on your body is the skin problem located?"
    },

    {
        "section": "skin_history",
        "field": "appearance",
        "question": "What does the affected area look like?"
    },

    {
        "section": "skin_history",
        "field": "itching",
        "question": "Is the area itchy?"
    },

    {
        "section": "skin_history",
        "field": "skin_pain",
        "question": "Is the affected area painful or tender?"
    },

    {
        "section": "skin_history",
        "field": "changes",
        "question": "Have you noticed any changes in the skin problem over time?"
    }

]


# =========================================================
# URINARY QUESTIONS
# =========================================================

URINARY_QUESTIONS = [

    {
        "section": "urinary_history",
        "field": "urination_changes",
        "question": "Have you noticed any changes in how often you urinate?"
    },

    {
        "section": "urinary_history",
        "field": "burning",
        "question": "Do you experience burning or pain while urinating?"
    },

    {
        "section": "urinary_history",
        "field": "blood",
        "question": "Have you noticed any blood in your urine?"
    },

    {
        "section": "urinary_history",
        "field": "urgency",
        "question": "Do you feel a sudden or urgent need to urinate?"
    },

    {
        "section": "urinary_history",
        "field": "urinary_associated_symptoms",
        "question": "Have you experienced fever, back pain, or other symptoms along with the urinary problem?"
    }

]


# =========================================================
# GENERAL MEDICAL HISTORY
# =========================================================

GENERAL_HISTORY_QUESTIONS = [

    {
        "section": "past_history",
        "field": "medical_history",
        "question": "Do you have any previous medical conditions?"
    },

    {
        "section": "past_history",
        "field": "surgical_history",
        "question": "Have you had any previous surgeries?"
    },

    {
        "section": "medication_history",
        "field": "current_medications",
        "question": "Are you currently taking any medicines?"
    },

    {
        "section": "medication_history",
        "field": "allergies",
        "question": "Do you have any known medicine, food, or other allergies?"
    },

    {
        "section": "family_history",
        "field": "family_history",
        "question": "Does anyone in your family have any important medical conditions?"
    },

    {
        "section": "personal_history",
        "field": "diet",
        "question": "How would you describe your usual diet?"
    },

    {
        "section": "personal_history",
        "field": "sleep",
        "question": "How has your sleep been recently?"
    },

    {
        "section": "personal_history",
        "field": "smoking",
        "question": "Do you smoke or use tobacco?"
    },

    {
        "section": "personal_history",
        "field": "alcohol",
        "question": "Do you consume alcohol?"
    },

    {
        "section": "personal_history",
        "field": "activity",
        "question": "How would you describe your usual physical activity?"
    }

]


# =========================================================
# REVIEW OF SYSTEMS
# =========================================================

ROS_QUESTIONS = [

    {
        "section": "review_of_systems",
        "field": "general",
        "question": "Have you recently experienced fever, unusual tiredness, or unexpected weight change?"
    },

    {
        "section": "review_of_systems",
        "field": "respiratory",
        "question": "Have you experienced cough, breathing difficulty, or wheezing?"
    },

    {
        "section": "review_of_systems",
        "field": "cardiovascular",
        "question": "Have you experienced palpitations, chest discomfort, or swelling of your legs?"
    },

    {
        "section": "review_of_systems",
        "field": "gastrointestinal",
        "question": "Have you experienced nausea, vomiting, diarrhea, constipation, or other digestive problems?"
    },

    {
        "section": "review_of_systems",
        "field": "neurological",
        "question": "Have you experienced dizziness, weakness, numbness, or severe headaches?"
    }

]


# =========================================================
# AYUSH / DASHAVIDHA QUESTIONS
# =========================================================

# The SIH requirement is represented as explicit structured fields.
# The legacy `dashavidha` field is retained for backward compatibility.
AYUSH_QUESTIONS = [

    {
        "section": "ayush",
        "field": "prakriti",
        "question": "If applicable, please describe your known Prakriti."
    },

    {
        "section": "ayush",
        "field": "vikriti",
        "question": "If applicable, please describe your known Vikriti or current imbalance assessment."
    },

    {
        "section": "ayush",
        "field": "sara",
        "question": "If known, please provide your Sara assessment."
    },

    {
        "section": "ayush",
        "field": "samhanana",
        "question": "If known, please provide your Samhanana assessment."
    },

    {
        "section": "ayush",
        "field": "pramana",
        "question": "If known, please provide your Pramana or body-measurement assessment."
    },

    {
        "section": "ayush",
        "field": "satmya",
        "question": "If known, please describe your Satmya or habituation assessment."
    },

    {
        "section": "ayush",
        "field": "sattva",
        "question": "If known, please provide your Sattva assessment."
    },

    {
        "section": "ayush",
        "field": "ahara_shakti",
        "question": "If known, please provide your Ahara Shakti assessment."
    },

    {
        "section": "ayush",
        "field": "vyayama_shakti",
        "question": "If known, please provide your Vyayama Shakti assessment."
    },

    {
        "section": "ayush",
        "field": "vaya",
        "question": "If known, please provide your Vaya assessment."
    },

    {
        "section": "ayush",
        "field": "ahara_vihara",
        "question": "Please describe any relevant Ahara-Vihara (diet and lifestyle) information."
    },

    {
        "section": "ayush",
        "field": "dashavidha",
        "question": "If applicable, please provide any other known Dashavidha Pariksha information."
    }
]


# =========================================================
# QUESTION GROUP MAP
# =========================================================

QUESTION_GROUPS = {

    "core": CORE_QUESTIONS,

    "pain": PAIN_QUESTIONS,

    "respiratory": RESPIRATORY_QUESTIONS,

    "gastrointestinal": GASTROINTESTINAL_QUESTIONS,

    "neurological": NEUROLOGICAL_QUESTIONS,

    "skin": SKIN_QUESTIONS,

    "urinary": URINARY_QUESTIONS,

    "general": (
        GENERAL_HISTORY_QUESTIONS
        + ROS_QUESTIONS
        + [
            {
                "section": "general_history",
                "field": "general_complaint",
                "question": "Apart from what you have already mentioned, is there anything else you would like to tell the doctor?"
            }
        ]
    ),

    "ayush": AYUSH_QUESTIONS,
}
from __future__ import annotations

import json
import re
from typing import Any

STATE_SIGNAL_NAME = "_interview_state"

SECTION_ORDER = (
    "hpi",
    "past_history",
    "drug_allergy",
    "family_history",
    "personal_history",
    "review_of_systems",
)

AYUSH_SECTION = "ayush"
ALL_SECTIONS = (*SECTION_ORDER, AYUSH_SECTION)

SECTION_QUESTION_BUDGETS = {
    "hpi": 3,
    "past_history": 1,
    "drug_allergy": 1,
    "family_history": 1,
    "personal_history": 1,
    "review_of_systems": 1,
    "ayush": 1,
}

HPI_FIELDS = {
    "chief_complaint",
    "onset",
    "course",
    "duration",
    "site",
    "laterality",
    "severity",
    "character",
    "timing",
    "frequency",
    "aggravating_factors",
    "relieving_factors",
    "radiation",
    "associated_symptoms",
    "previous_episodes",
    "impact_on_daily_life",
    "prior_treatment",
    "response_to_treatment",
    "prior_investigations",
    "constitutional",
    "cardiovascular",
    "respiratory",
    "gastrointestinal",
    "genitourinary",
    "neurological",
    "musculoskeletal",
    "skin",
    "endocrine",
    "hematologic",
    "psychiatric",
    "breathing_difficulty",
    "nausea_vomiting",
    "vision_or_neuro",
    "cough",
    "wheeze",
    "fever",
    "fatigue",
    "weight_change",
    "bowel_changes",
    "bowel_frequency",
    "stool_consistency",
    "straining",
    "blood_in_stool",
    "abdominal_distension",
    "urinary_frequency",
    "urinary_burning",
    "urinary_blood",
}

HISTORY_FIELDS = {
    "past_medical_history",
    "past_surgical_history",
    "hospitalizations",
    "immunizations",
    "medications",
    "allergies",
    "adverse_drug_reactions",
    "family_history",
    "personal_history",
    "occupation",
    "diet",
    "sleep",
    "physical_activity",
    "smoking",
    "alcohol",
    "tobacco",
    "menstrual_history",
    "pregnancy_status",
    "sexual_history",
    "review_of_systems",
}

AYUSH_FIELDS = {
    "ayush_prakriti",
    "ayush_vikriti",
    "ayush_sara",
    "ayush_samhanana",
    "ayush_pramana",
    "ayush_satmya",
    "ayush_satva",
    "ayush_ahara_shakti",
    "ayush_vyayama_shakti",
    "ayush_vaya",
    "ayush_ahara_vihara",
    "ayush_agni",
    "ayush_koshta",
    "ayush_nidana",
    "ayush_samprapti",
}

KNOWN_FIELDS = HPI_FIELDS | HISTORY_FIELDS | AYUSH_FIELDS

FIELD_ALIASES = {
    "complaint": "chief_complaint",
    "main_complaint": "chief_complaint",
    "main_problem": "chief_complaint",
    "problem": "chief_complaint",
    "symptom": "chief_complaint",
    "started": "onset",
    "start": "onset",
    "when_started": "onset",
    "how_long": "duration",
    "progression": "course",
    "pattern": "timing",
    "pain_score": "severity",
    "pain_level": "severity",
    "intensity": "severity",
    "pain_type": "character",
    "quality": "character",
    "location": "site",
    "where": "site",
    "place": "site",
    "side": "laterality",
    "worse_with": "aggravating_factors",
    "aggravated_by": "aggravating_factors",
    "better_with": "relieving_factors",
    "relieved_by": "relieving_factors",
    "radiates_to": "radiation",
    "associated": "associated_symptoms",
    "other_symptoms": "associated_symptoms",
    "family": "family_history",
    "social_history": "personal_history",
    "lifestyle": "personal_history",
    "occupation_history": "occupation",
    "smoking_history": "smoking",
    "tobacco_use": "tobacco",
    "alcohol_use": "alcohol",
    "exercise": "physical_activity",
    "diet_history": "diet",
    "sleep_history": "sleep",
    "ros": "review_of_systems",
    "review_of_system": "review_of_systems",
    "medical_history": "past_medical_history",
    "past_history": "past_medical_history",
    "surgical_history": "past_surgical_history",
    "surgery_history": "past_surgical_history",
    "operations": "past_surgical_history",
    "hospital_history": "hospitalizations",
    "current_medications": "medications",
    "drugs": "medications",
    "drug_history": "medications",
    "drug_allergies": "allergies",
    "medicine_allergies": "allergies",
    "adverse_reactions": "adverse_drug_reactions",
    "investigations": "prior_investigations",
    "previous_tests": "prior_investigations",
    "prior_tests": "prior_investigations",
    "treatment_history": "prior_treatment",
    "treatment_response": "response_to_treatment",
    "breathlessness": "breathing_difficulty",
    "shortness_of_breath": "breathing_difficulty",
    "difficulty_breathing": "breathing_difficulty",
    "nausea": "nausea_vomiting",
    "vomiting": "nausea_vomiting",
    "nausea_or_vomiting": "nausea_vomiting",
    "vision": "vision_or_neuro",
    "neurological_symptoms": "vision_or_neuro",
    "coughing": "cough",
    "wheezing": "wheeze",
    "itching": "skin",
    "painful_urination": "urinary_burning",
    "burning_urination": "urinary_burning",
    "blood_in_urine": "urinary_blood",
    "rectal_bleeding": "blood_in_stool",
    "blood_in_stools": "blood_in_stool",
    "bowel_problem": "bowel_changes",
    "constipation": "bowel_changes",
    "constipated": "bowel_changes",
    "stool_frequency": "bowel_frequency",
    "stool_type": "stool_consistency",
    "abdominal_bloating": "abdominal_distension",
    "bloating": "abdominal_distension",
    "menstrual": "menstrual_history",
    "periods": "menstrual_history",
    "sexual": "sexual_history",
    "prakriti": "ayush_prakriti",
    "vikriti": "ayush_vikriti",
    "sara": "ayush_sara",
    "samhanana": "ayush_samhanana",
    "pramana": "ayush_pramana",
    "satmya": "ayush_satmya",
    "satva": "ayush_satva",
    "ahara_shakti": "ayush_ahara_shakti",
    "vyayama_shakti": "ayush_vyayama_shakti",
    "vaya": "ayush_vaya",
    "agni": "ayush_agni",
    "koshta": "ayush_koshta",
    "ahara_vihara": "ayush_ahara_vihara",
    "nidana": "ayush_nidana",
    "samprapti": "ayush_samprapti",
}

FIELD_PRIMARY_SECTION = {
    **{field: "hpi" for field in HPI_FIELDS},
    **{
        field: "past_history"
        for field in {
            "past_medical_history",
            "past_surgical_history",
            "hospitalizations",
            "immunizations",
        }
    },
    **{
        field: "drug_allergy"
        for field in {
            "medications",
            "allergies",
            "adverse_drug_reactions",
        }
    },
    "family_history": "family_history",
    **{
        field: "personal_history"
        for field in {
            "personal_history",
            "occupation",
            "diet",
            "sleep",
            "physical_activity",
            "smoking",
            "alcohol",
            "tobacco",
            "menstrual_history",
            "pregnancy_status",
            "sexual_history",
        }
    },
    "review_of_systems": "review_of_systems",
    **{
        field: "ayush"
        for field in AYUSH_FIELDS
    },
}

MULTI_VALUE_FIELDS = {
    "past_medical_history",
    "past_surgical_history",
    "hospitalizations",
    "immunizations",
    "medications",
    "allergies",
    "adverse_drug_reactions",
    "family_history",
    "personal_history",
    "associated_symptoms",
    "prior_treatment",
    "prior_investigations",
    "review_of_systems",
    "aggravating_factors",
    "relieving_factors",
    "radiation",
}

TARGET_FIELDS = {
    "chief_complaint": ("chief_complaint",),
    "onset": ("onset",),
    "duration": ("duration",),
    "course": ("course",),
    "site": ("site",),
    "laterality": ("laterality",),
    "severity": ("severity",),
    "character": ("character",),
    "timing": ("timing",),
    "frequency": ("frequency",),
    "aggravating_factors": ("aggravating_factors",),
    "relieving_factors": ("relieving_factors",),
    "radiation": ("radiation",),
    "associated_symptoms": ("associated_symptoms",),
    "previous_episodes": ("previous_episodes",),
    "prior_treatment": ("prior_treatment",),
    "response_to_treatment": ("response_to_treatment",),
    "prior_investigations": ("prior_investigations",),
    "impact_on_daily_life": ("impact_on_daily_life",),
    "breathing_difficulty": ("breathing_difficulty",),
    "nausea_vomiting": ("nausea_vomiting",),
    "vision_or_neuro": ("vision_or_neuro",),
    "cough": ("cough",),
    "wheeze": ("wheeze",),
    "fever": ("fever",),
    "bowel_frequency": ("bowel_frequency",),
    "stool_consistency": ("stool_consistency",),
    "straining": ("straining",),
    "blood_in_stool": ("blood_in_stool",),
    "abdominal_distension": ("abdominal_distension",),
    "urinary_frequency": ("urinary_frequency",),
    "urinary_burning": ("urinary_burning",),
    "urinary_blood": ("urinary_blood",),
    "past_medical_history": ("past_medical_history",),
    "past_surgical_history": ("past_surgical_history",),
    "hospitalizations": ("hospitalizations",),
    "immunizations": ("immunizations",),
    "medications": ("medications",),
    "allergies": ("allergies",),
    "adverse_drug_reactions": ("adverse_drug_reactions",),
    "family_history": ("family_history",),
    "occupation": ("occupation",),
    "diet": ("diet",),
    "sleep": ("sleep",),
    "physical_activity": ("physical_activity",),
    "smoking": ("smoking",),
    "alcohol": ("alcohol",),
    "tobacco": ("tobacco",),
    "menstrual_history": ("menstrual_history",),
    "pregnancy_status": ("pregnancy_status",),
    "sexual_history": ("sexual_history",),
    "constitutional": ("constitutional",),
    "cardiovascular": ("cardiovascular",),
    "respiratory": ("respiratory",),
    "gastrointestinal": ("gastrointestinal",),
    "genitourinary": ("genitourinary",),
    "neurological": ("neurological",),
    "musculoskeletal": ("musculoskeletal",),
    "skin": ("skin",),
    "endocrine": ("endocrine",),
    "hematologic": ("hematologic",),
    "psychiatric": ("psychiatric",),
    "ayush_prakriti": ("ayush_prakriti",),
    "ayush_vikriti": ("ayush_vikriti",),
    "ayush_sara": ("ayush_sara",),
    "ayush_samhanana": ("ayush_samhanana",),
    "ayush_pramana": ("ayush_pramana",),
    "ayush_satmya": ("ayush_satmya",),
    "ayush_satva": ("ayush_satva",),
    "ayush_ahara_shakti": ("ayush_ahara_shakti",),
    "ayush_vyayama_shakti": ("ayush_vyayama_shakti",),
    "ayush_vaya": ("ayush_vaya",),
    "ayush_ahara_vihara": ("ayush_ahara_vihara",),
    "ayush_agni": ("ayush_agni",),
    "ayush_koshta": ("ayush_koshta",),
    "ayush_nidana": ("ayush_nidana",),
    "ayush_samprapti": ("ayush_samprapti",),
}

TARGET_DESCRIPTIONS = {
    "chief_complaint": {"en": "the main problem or symptom that brought you here", "hi": "मुख्य समस्या या लक्षण जिसके कारण आप आए हैं"},
    "onset": {"en": "when the current problem started", "hi": "यह समस्या कब शुरू हुई"},
    "duration": {"en": "how long the current problem has been present", "hi": "यह समस्या कितने समय से है"},
    "course": {"en": "how the problem has changed over time", "hi": "समय के साथ यह समस्या कैसे बदली है"},
    "site": {"en": "where the symptom is located", "hi": "यह लक्षण शरीर में कहाँ है"},
    "laterality": {"en": "which side is affected", "hi": "समस्या शरीर के किस तरफ है"},
    "severity": {"en": "how severe the symptom is", "hi": "लक्षण की तीव्रता कितनी है"},
    "character": {"en": "what the symptom feels like", "hi": "लक्षण कैसा महसूस होता है"},
    "timing": {"en": "the timing or pattern of the symptom", "hi": "लक्षण का समय या पैटर्न"},
    "frequency": {"en": "how often the symptom occurs", "hi": "लक्षण कितनी बार होता है"},
    "aggravating_factors": {"en": "what makes the symptom worse", "hi": "किस चीज़ से लक्षण बढ़ता है"},
    "relieving_factors": {"en": "what makes the symptom better", "hi": "किस चीज़ से लक्षण कम होता है"},
    "radiation": {"en": "whether the symptom spreads anywhere else", "hi": "क्या लक्षण कहीं और फैलता है"},
    "associated_symptoms": {"en": "other symptoms occurring with the main problem", "hi": "मुख्य समस्या के साथ होने वाले अन्य लक्षण"},
    "previous_episodes": {"en": "whether this has happened before", "hi": "क्या यह समस्या पहले भी हुई है"},
    "prior_treatment": {"en": "what treatment or self-care has already been tried", "hi": "अब तक कौन सा इलाज या स्वयं की देखभाल की गई है"},
    "response_to_treatment": {"en": "how previous treatment affected the problem", "hi": "पहले किए गए इलाज से क्या असर हुआ"},
    "prior_investigations": {"en": "any previous tests or investigations for this problem", "hi": "इस समस्या के लिए पहले हुई जाँच या परीक्षण"},
    "impact_on_daily_life": {"en": "how the problem affects normal daily activities", "hi": "यह समस्या रोज़मर्रा के काम पर कैसे असर डालती है"},
    "breathing_difficulty": {"en": "any difficulty with breathing", "hi": "साँस लेने में कोई परेशानी"},
    "nausea_vomiting": {"en": "nausea or vomiting", "hi": "मतली या उल्टी"},
    "vision_or_neuro": {"en": "visual or neurological symptoms", "hi": "दृष्टि या नसों से जुड़े लक्षण"},
    "cough": {"en": "cough or related respiratory symptoms", "hi": "खाँसी या उससे जुड़े श्वसन लक्षण"},
    "wheeze": {"en": "wheezing", "hi": "सीटी जैसी साँस या घरघराहट"},
    "fever": {"en": "fever or chills", "hi": "बुखार या ठंड लगना"},
    "bowel_frequency": {"en": "bowel movement frequency", "hi": "मल त्याग की आवृत्ति"},
    "stool_consistency": {"en": "stool consistency", "hi": "मल की बनावट"},
    "straining": {"en": "straining during bowel movements", "hi": "मल त्याग के समय जोर लगाना"},
    "blood_in_stool": {"en": "blood in or on the stool", "hi": "मल में या मल पर खून"},
    "abdominal_distension": {"en": "bloating or abdominal swelling", "hi": "पेट में फूलना या सूजन"},
    "urinary_frequency": {"en": "how often you urinate", "hi": "पेशाब कितनी बार आता है"},
    "urinary_burning": {"en": "burning or pain while urinating", "hi": "पेशाब करते समय जलन या दर्द"},
    "urinary_blood": {"en": "blood in the urine", "hi": "पेशाब में खून"},
    "past_medical_history": {"en": "previous medical conditions or diagnoses", "hi": "पहले की महत्वपूर्ण बीमारियाँ या निदान"},
    "past_surgical_history": {"en": "previous operations or surgeries", "hi": "पहले हुई सर्जरी या ऑपरेशन"},
    "hospitalizations": {"en": "previous hospital admissions", "hi": "पहले अस्पताल में भर्ती होने का इतिहास"},
    "immunizations": {"en": "relevant immunization history", "hi": "टीकाकरण का प्रासंगिक इतिहास"},
    "medications": {"en": "current medicines or supplements", "hi": "अभी ली जा रही दवाएँ या सप्लीमेंट"},
    "allergies": {"en": "medicine, food, or other allergies", "hi": "दवा, भोजन या अन्य एलर्जी"},
    "adverse_drug_reactions": {"en": "previous adverse reactions to medicines", "hi": "दवाओं से पहले हुई प्रतिकूल प्रतिक्रियाएँ"},
    "family_history": {"en": "important medical conditions in the family", "hi": "परिवार में महत्वपूर्ण बीमारियों का इतिहास"},
    "occupation": {"en": "your work or occupation", "hi": "आपका काम या व्यवसाय"},
    "diet": {"en": "usual diet", "hi": "आपका सामान्य भोजन"},
    "sleep": {"en": "usual sleep pattern", "hi": "आपकी सामान्य नींद का पैटर्न"},
    "physical_activity": {"en": "usual physical activity or exercise", "hi": "आपकी सामान्य शारीरिक गतिविधि या व्यायाम"},
    "smoking": {"en": "smoking or cigarette use", "hi": "धूम्रपान या सिगरेट का उपयोग"},
    "alcohol": {"en": "alcohol use", "hi": "शराब का सेवन"},
    "tobacco": {"en": "other tobacco use", "hi": "अन्य तंबाकू का उपयोग"},
    "menstrual_history": {"en": "menstrual history when relevant", "hi": "प्रासंगिक होने पर मासिक धर्म का इतिहास"},
    "pregnancy_status": {"en": "pregnancy status when relevant", "hi": "प्रासंगिक होने पर गर्भावस्था की स्थिति"},
    "sexual_history": {"en": "sexual health history when relevant", "hi": "प्रासंगिक होने पर यौन स्वास्थ्य का इतिहास"},
    "constitutional": {"en": "general or constitutional symptoms", "hi": "सामान्य या संवैधानिक लक्षण"},
    "cardiovascular": {"en": "cardiovascular symptoms", "hi": "हृदय या रक्तसंचार से जुड़े लक्षण"},
    "respiratory": {"en": "respiratory symptoms", "hi": "श्वसन तंत्र से जुड़े लक्षण"},
    "gastrointestinal": {"en": "gastrointestinal symptoms", "hi": "पाचन तंत्र से जुड़े लक्षण"},
    "genitourinary": {"en": "genitourinary symptoms", "hi": "मूत्र या जनन तंत्र से जुड़े लक्षण"},
    "neurological": {"en": "neurological symptoms", "hi": "तंत्रिका तंत्र से जुड़े लक्षण"},
    "musculoskeletal": {"en": "musculoskeletal symptoms", "hi": "मांसपेशियों या जोड़ों से जुड़े लक्षण"},
    "skin": {"en": "skin symptoms", "hi": "त्वचा से जुड़े लक्षण"},
    "endocrine": {"en": "endocrine symptoms", "hi": "अंतःस्रावी तंत्र से जुड़े लक्षण"},
    "hematologic": {"en": "blood-related symptoms", "hi": "रक्त से जुड़े लक्षण"},
    "psychiatric": {"en": "mental or emotional symptoms", "hi": "मानसिक या भावनात्मक लक्षण"},
    "ayush_prakriti": {"en": "Prakriti", "hi": "प्रकृति"},
    "ayush_vikriti": {"en": "Vikriti", "hi": "विकृति"},
    "ayush_sara": {"en": "Sara", "hi": "सार"},
    "ayush_samhanana": {"en": "Samhanana", "hi": "संहनन"},
    "ayush_pramana": {"en": "Pramana", "hi": "प्रमाण"},
    "ayush_satmya": {"en": "Satmya", "hi": "सात्म्य"},
    "ayush_satva": {"en": "Satva", "hi": "सत्त्व"},
    "ayush_ahara_shakti": {"en": "Ahara Shakti", "hi": "आहार शक्ति"},
    "ayush_vyayama_shakti": {"en": "Vyayama Shakti", "hi": "व्यायाम शक्ति"},
    "ayush_vaya": {"en": "Vaya", "hi": "वय"},
    "ayush_ahara_vihara": {"en": "Ahara-Vihara", "hi": "आहार-विहार"},
    "ayush_agni": {"en": "Agni", "hi": "अग्नि"},
    "ayush_koshta": {"en": "Koshtha", "hi": "कोष्ठ"},
    "ayush_nidana": {"en": "Nidana", "hi": "निदान"},
    "ayush_samprapti": {"en": "Samprapti", "hi": "सम्प्राप्ति"},
}

HPI_CORE_GROUPS = (
    ("onset", "duration"),
    ("course",),
    ("site", "laterality"),
    ("severity", "impact_on_daily_life"),
    ("character",),
    ("radiation",),
    ("aggravating_factors", "relieving_factors"),
    ("associated_symptoms",),
    ("previous_episodes", "prior_treatment", "prior_investigations"),
    ("timing", "frequency"),
)

PAST_REQUIRED = (
    "past_medical_history",
    "past_surgical_history",
    "hospitalizations",
)

DRUG_REQUIRED = (
    "medications",
    "allergies",
    "adverse_drug_reactions",
)

PERSONAL_GROUPS = (
    "occupation",
    "diet",
    "sleep",
    "physical_activity",
    "smoking",
    "alcohol",
    "tobacco",
)

PERSONAL_OPTIONAL_GROUPS = (
    "menstrual_history",
    "pregnancy_status",
    "sexual_history",
)

ROS_TARGETS = (
    "constitutional",
    "cardiovascular",
    "respiratory",
    "gastrointestinal",
    "genitourinary",
    "neurological",
    "musculoskeletal",
    "skin",
    "endocrine",
    "hematologic",
    "psychiatric",
)

AYUSH_REQUIRED = (
    "ayush_prakriti",
    "ayush_vikriti",
    "ayush_sara",
    "ayush_samhanana",
    "ayush_pramana",
    "ayush_satmya",
    "ayush_satva",
    "ayush_ahara_shakti",
    "ayush_vyayama_shakti",
    "ayush_vaya",
    "ayush_ahara_vihara",
    "ayush_agni",
    "ayush_koshta",
    "ayush_nidana",
    "ayush_samprapti",
)

DETAIL_REQUIRED = {
    "chief_complaint",
    "past_medical_history",
    "past_surgical_history",
    "hospitalizations",
    "medications",
    "allergies",
    "adverse_drug_reactions",
    "family_history",
    "occupation",
    "diet",
    "sleep",
    "physical_activity",
    "smoking",
    "alcohol",
    "tobacco",
    "menstrual_history",
    "pregnancy_status",
    "sexual_history",
}


def normalize_section(section: str | None) -> str:
    value = (
        str(section or "hpi")
        .strip()
        .lower()
        .replace("-", "_")
    )

    if value == "medical_history":
        return "past_history"

    if value == "drug_history":
        return "drug_allergy"

    return (
        value
        if value in ALL_SECTIONS
        else "hpi"
    )


def slugify(value: str) -> str:
    result = re.sub(
        r"[^a-z0-9_]+",
        "_",
        value.lower(),
    ).strip("_")

    return result[:80] or "fact"


def normalize_field_name(
    name: str | None,
) -> str:
    value = (
        str(name or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    if value in KNOWN_FIELDS:
        return value

    return (
        FIELD_ALIASES.get(value)
        or f"custom_{slugify(value)}"
    )


def _clean_value(
    value: Any,
) -> Any:
    if isinstance(value, str):
        return " ".join(
            value.strip().split()
        )

    if isinstance(value, list):
        return [
            item
            for item in (
                _clean_value(item)
                for item in value
            )
            if item not in (None, "")
        ]

    if isinstance(value, dict):
        return {
            str(key): _clean_value(item)
            for key, item in value.items()
        }

    return value


def _value_key(
    value: Any,
) -> str:
    return json.dumps(
        _clean_value(value),
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    ).lower()


class InterviewState:
    VERSION = 3

    def __init__(
        self,
        topic: str = "general",
        current_section: str = "hpi",
        ayush_enabled: bool = False,
        completed_sections: set[str] | None = None,
        facts: list[dict[str, Any]] | None = None,
        question_history: list[str] | None = None,
        target_history: list[str] | None = None,
        pending_target: str | None = None,
        closure_asked_sections: set[str] | None = None,
        turn_count: int = 0,
    ) -> None:
        self.topic = (
            topic.strip()
            or "general"
        )
        self.current_section = normalize_section(
            current_section
        )
        self.ayush_enabled = bool(
            ayush_enabled
        )
        self.completed_sections = {
            normalize_section(item)
            for item in (
                completed_sections or set()
            )
            if normalize_section(item)
            in ALL_SECTIONS
        }
        self.facts = list(
            facts or []
        )
        self.question_history = [
            str(item).strip()
            for item in (
                question_history or []
            )
            if str(item).strip()
        ]
        self.target_history = [
            str(item).strip()
            for item in (
                target_history or []
            )
            if str(item).strip()
        ]
        self.pending_target = (
            pending_target
            if pending_target
            else None
        )
        self.closure_asked_sections = {
            normalize_section(item)
            for item in (
                closure_asked_sections or set()
            )
            if normalize_section(item)
            in ALL_SECTIONS
        }
        self.turn_count = int(
            turn_count or 0
        )

    @classmethod
    def empty(
        cls,
        ayush_enabled: bool = False,
    ) -> "InterviewState":
        return cls(
            ayush_enabled=ayush_enabled
        )

    @classmethod
    def from_value(
        cls,
        value: Any,
        legacy_fields: dict[str, Any] | None = None,
        ayush_enabled: bool = False,
    ) -> "InterviewState":
        parsed = None

        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = None
        elif isinstance(value, dict):
            parsed = value

        if (
            isinstance(parsed, dict)
            and parsed.get("version") == cls.VERSION
        ):
            return cls(
                topic=str(
                    parsed.get("topic")
                    or "general"
                ),
                current_section=str(
                    parsed.get("current_section")
                    or "hpi"
                ),
                ayush_enabled=bool(
                    ayush_enabled
                    or parsed.get(
                        "ayush_enabled",
                        False,
                    )
                ),
                completed_sections=set(
                    parsed.get(
                        "completed_sections",
                        [],
                    )
                ),
                facts=parsed.get(
                    "facts",
                    [],
                ),
                question_history=parsed.get(
                    "question_history",
                    [],
                ),
                target_history=parsed.get(
                    "target_history",
                    [],
                ),
                pending_target=parsed.get(
                    "pending_target"
                ),
                closure_asked_sections=set(
                    parsed.get(
                        "closure_asked_sections",
                        [],
                    )
                ),
                turn_count=int(
                    parsed.get(
                        "turn_count",
                        0,
                    )
                    or 0
                ),
            )

        state = cls.empty(
            ayush_enabled=ayush_enabled
        )

        if isinstance(parsed, dict):
            state.topic = str(
                parsed.get(
                    "topic",
                    "general",
                )
                or "general"
            )
            state.current_section = normalize_section(
                str(
                    parsed.get(
                        "current_section",
                        "hpi",
                    )
                    or "hpi"
                )
            )
            state.ayush_enabled = bool(
                ayush_enabled
                or parsed.get(
                    "ayush_enabled",
                    False,
                )
            )
            state.completed_sections = {
                normalize_section(item)
                for item in parsed.get(
                    "completed_sections",
                    [],
                )
                if normalize_section(item)
                in ALL_SECTIONS
            }
            state.facts = list(
                parsed.get(
                    "facts",
                    [],
                )
            )

        if legacy_fields:
            legacy_completed = legacy_fields.get(
                "_interview_completed_sections"
            )

            if (
                not state.completed_sections
                and legacy_completed
            ):
                if isinstance(
                    legacy_completed,
                    str,
                ):
                    try:
                        legacy_completed = json.loads(
                            legacy_completed
                        )
                    except json.JSONDecodeError:
                        legacy_completed = legacy_completed.split(
                            ","
                        )

                if isinstance(
                    legacy_completed,
                    (list, set, tuple),
                ):
                    state.mark_sections(
                        list(
                            legacy_completed
                        )
                    )

            legacy_section = legacy_fields.get(
                "_interview_section"
            )

            if legacy_section:
                state.current_section = normalize_section(
                    str(
                        legacy_section
                    )
                )

            legacy_topic = legacy_fields.get(
                "symptom_topic"
            )

            if (
                legacy_topic
                and state.topic == "general"
            ):
                state.topic = (
                    str(
                        legacy_topic
                    ).strip()
                    or state.topic
                )

            if not state.facts:
                for field, value_item in legacy_fields.items():
                    if (
                        field.startswith("_")
                        or field == "symptom_topic"
                    ):
                        continue

                    state.add_fact(
                        FIELD_PRIMARY_SECTION.get(
                            field,
                            "hpi",
                        ),
                        field,
                        value_item,
                        None,
                        None,
                        False,
                    )

        state.question_history = []
        state.target_history = []
        state.pending_target = None
        state.closure_asked_sections = set()
        state.turn_count = 0

        return state

    def to_value(self) -> str:
        return json.dumps(
            {
                "version": self.VERSION,
                "topic": self.topic,
                "current_section": self.current_section,
                "ayush_enabled": self.ayush_enabled,
                "completed_sections": sorted(
                    self.completed_sections
                ),
                "facts": self.facts[-300:],
                "question_history": self.question_history[-40:],
                "target_history": self.target_history[-40:],
                "pending_target": self.pending_target,
                "closure_asked_sections": sorted(
                    self.closure_asked_sections
                ),
                "turn_count": self.turn_count,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def add_fact(
        self,
        section: str,
        field: str,
        value: Any,
        evidence: str | None,
        turn_id: str | None,
        negative: bool = False,
    ) -> None:
        normalized_section = normalize_section(
            section
        )
        normalized_field = normalize_field_name(
            field
        )
        cleaned_value = _clean_value(
            value
        )

        if cleaned_value in (
            None,
            "",
            [],
        ):
            return

        fact = {
            "section": normalized_section,
            "field": normalized_field,
            "value": cleaned_value,
            "negative": bool(negative),
            "evidence": evidence,
            "turn_id": turn_id,
        }

        key = (
            normalized_section,
            normalized_field,
            _value_key(cleaned_value),
            bool(negative),
        )

        existing_keys = {
            (
                item.get("section"),
                item.get("field"),
                _value_key(
                    item.get("value")
                ),
                bool(
                    item.get(
                        "negative"
                    )
                ),
            )
            for item in self.facts
        }

        if key not in existing_keys:
            self.facts.append(fact)

    def add_facts(
        self,
        facts: list[dict[str, Any]],
        evidence: str | None,
        turn_id: str | None,
    ) -> None:
        for fact in facts:
            if not isinstance(
                fact,
                dict,
            ):
                continue

            self.add_fact(
                str(
                    fact.get(
                        "section"
                    )
                    or self.current_section
                ),
                str(
                    fact.get(
                        "field"
                    )
                    or ""
                ),
                fact.get(
                    "value"
                ),
                str(
                    fact.get(
                        "evidence"
                    )
                    or evidence
                    or ""
                ).strip()
                or None,
                turn_id,
                bool(
                    fact.get(
                        "negative",
                        False,
                    )
                ),
            )

    def add_question(
        self,
        question: str | None,
        target: str | None = None,
    ) -> None:
        if not question:
            return

        value = " ".join(
            question.strip().split()
        )

        if not value:
            return

        def question_key(item: str) -> str:
            normalized = re.sub(
                r"[^a-z0-9\u0900-\u097f]+",
                " ",
                item.lower(),
                flags=re.IGNORECASE,
            )
            return " ".join(
                normalized.split()
            )

        current_key = question_key(
            value
        )

        if (
            not any(
                question_key(item)
                == current_key
                for item in self.question_history
            )
        ):
            self.question_history.append(
                value
            )
            self.target_history.append(
                str(
                    target or ""
                ).strip()
            )

        self.pending_target = (
            target
            if target
            else None
        )

    def mark_sections(
        self,
        sections: list[str]
        | set[str]
        | None,
    ) -> None:
        for section in (
            sections or []
        ):
            normalized = normalize_section(
                section
            )

            if normalized in ALL_SECTIONS:
                self.completed_sections.add(
                    normalized
                )

    def complete_current_section(
        self,
    ) -> None:
        self.completed_sections.add(
            self.current_section
        )
        self.closure_asked_sections.discard(
            self.current_section
        )
        self.pending_target = None

        next_section = self.next_section()

        self.current_section = (
            next_section
            or self.current_section
        )

    def next_section(
        self,
    ) -> str | None:
        for section in SECTION_ORDER:
            if (
                section
                not in self.completed_sections
            ):
                return section

        if (
            self.ayush_enabled
            and AYUSH_SECTION
            not in self.completed_sections
        ):
            return AYUSH_SECTION

        return None

    def is_complete(self) -> bool:
        required = set(
            SECTION_ORDER
        )

        if self.ayush_enabled:
            required.add(
                AYUSH_SECTION
            )

        return required.issubset(
            self.completed_sections
        )

    def known_fields(self) -> dict[str, Any]:
        grouped: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for fact in self.facts:
            field = str(
                fact.get(
                    "field"
                )
                or ""
            )

            if field:
                grouped.setdefault(
                    field,
                    [],
                ).append(fact)

        result: dict[str, Any] = {}

        for field, facts in grouped.items():
            positives = [
                item.get("value")
                for item in facts
                if not item.get(
                    "negative"
                )
            ]

            negatives = [
                item.get("value")
                for item in facts
                if item.get(
                    "negative"
                )
            ]

            if positives:
                if field in MULTI_VALUE_FIELDS:
                    values: list[str] = []

                    for value in positives:
                        for item in (
                            value
                            if isinstance(
                                value,
                                list,
                            )
                            else [value]
                        ):
                            text = str(
                                item
                            ).strip()

                            if (
                                text
                                and text
                                not in values
                            ):
                                values.append(
                                    text
                                )

                    if values:
                        result[field] = (
                            values
                            if len(values) > 1
                            else values[0]
                        )
                else:
                    result[field] = positives[-1]

            elif negatives:
                result[field] = False

        return result

    def section_facts(
        self,
        section: str,
    ) -> list[dict[str, Any]]:
        normalized = normalize_section(
            section
        )

        return [
            fact
            for fact in self.facts
            if normalize_section(
                fact.get("section")
            )
            == normalized
        ]

    def target_value(
        self,
        target: str,
    ) -> Any:
        values = self.known_fields()
        fields = TARGET_FIELDS.get(
            target,
            (target,),
        )

        for field in fields:
            if field in values:
                return values[field]

        return None

    def target_answered(
        self,
        target: str,
    ) -> bool:
        value = self.target_value(
            target
        )

        if value is None:
            return False

        # False is a valid collected negative answer. Positive True on a
        # detail-required history field still needs the requested details.
        if isinstance(value, bool):
            if target in DETAIL_REQUIRED:
                return not value
            return True

        normalized = str(
            value
        ).strip().lower()

        # A patient may genuinely not know an AYUSH or medical-history
        # detail. Record that outcome once rather than looping on the question.
        if normalized in {
            "unknown",
            "not known",
            "not sure",
            "not available",
            "not reported",
            "पता नहीं",
            "मालूम नहीं",
            "मुझे नहीं पता",
            "नहीं पता",
        }:
            return True

        if target in DETAIL_REQUIRED:
            if normalized in {
                "yes",
                "y",
                "true",
                "haan",
                "ha",
                "हाँ",
                "हां",
                "haa",
            }:
                return False

        return True

    def _hpi_candidates(self) -> list[str]:
        if not self.target_answered(
            "chief_complaint"
        ):
            return [
                "chief_complaint"
            ]

        base = [
            "onset",
            "duration",
            "course",
            "site",
            "severity",
            "character",
            "timing",
            "frequency",
            "aggravating_factors",
            "relieving_factors",
            "associated_symptoms",
            "previous_episodes",
            "prior_treatment",
            "response_to_treatment",
            "prior_investigations",
            "impact_on_daily_life",
        ]

        topic = self.topic.lower()

        if "chest" in topic:
            base = [
                "onset",
                "duration",
                "site",
                "character",
                "radiation",
                "aggravating_factors",
                "relieving_factors",
                "associated_symptoms",
                "severity",
                "timing",
                "frequency",
                "previous_episodes",
                "prior_treatment",
                "response_to_treatment",
                "prior_investigations",
                "impact_on_daily_life",
            ]

        if topic in {
            "gastrointestinal",
            "constipation",
            "diarrhea",
        }:
            base.extend(
                [
                    "bowel_frequency",
                    "stool_consistency",
                    "straining",
                    "blood_in_stool",
                    "abdominal_distension",
                    "nausea_vomiting",
                ]
            )
        elif topic in {
            "respiratory",
            "breathing_difficulty",
        }:
            base.extend(
                [
                    "breathing_difficulty",
                    "cough",
                    "wheeze",
                    "fever",
                ]
            )
        elif topic in {
            "headache",
            "neurological",
        }:
            base.extend(
                [
                    "vision_or_neuro",
                    "nausea_vomiting",
                    "fever",
                ]
            )
        elif topic == "urinary":
            base.extend(
                [
                    "urinary_frequency",
                    "urinary_burning",
                    "urinary_blood",
                    "fever",
                ]
            )

        if topic in {
            "headache",
            "neurological",
            "musculoskeletal",
            "skin",
        }:
            base.insert(
                4,
                "laterality",
            )
        else:
            base.extend(
                [
                    "fever",
                    "nausea_vomiting",
                ]
            )

        return [
            target
            for target in dict.fromkeys(
                base
            )
            if not self.target_answered(
                target
            )
        ]

    @staticmethod
    def _prioritize_pending(
        targets: list[str],
        pending: list[str],
    ) -> list[str]:
        if not pending:
            return list(
                dict.fromkeys(
                    targets
                )
            )

        ordered = [
            *pending,
            *targets,
        ]

        return list(
            dict.fromkeys(
                item
                for item in ordered
                if item in targets
            )
        )

    def candidate_targets(self) -> list[str]:
        # Budgets guide question breadth; they never close a section while
        # required information is still missing.
        pending = [
            target
            for target in self._split_targets(
                self.pending_target
            )
            if not self.target_answered(target)
            and (
                FIELD_PRIMARY_SECTION.get(
                    target
                )
                == self.current_section
            )
        ]

        if self.current_section == "hpi":
            return self._prioritize_pending(
                self._hpi_candidates(),
                pending,
            )

        if self.current_section == "past_history":
            targets = [
                target
                for target in (
                    *PAST_REQUIRED,
                    "immunizations",
                )
                if not self.target_answered(
                    target
                )
            ]
            return self._prioritize_pending(
                list(
                    dict.fromkeys(
                        targets
                    )
                ),
                pending,
            )

        if self.current_section == "drug_allergy":
            targets = [
                target
                for target in DRUG_REQUIRED
                if not self.target_answered(
                    target
                )
            ]

            if (
                self.target_answered(
                    "medications"
                )
                and self.target_answered(
                    "allergies"
                )
                and not self.target_answered(
                    "adverse_drug_reactions"
                )
            ):
                targets.append(
                    "adverse_drug_reactions"
                )

            return self._prioritize_pending(
                list(
                    dict.fromkeys(
                        targets
                    )
                ),
                pending,
            )

        if self.current_section == "family_history":
            targets = (
                []
                if self.target_answered(
                    "family_history"
                )
                else [
                    "family_history"
                ]
            )
            return self._prioritize_pending(
                targets,
                pending,
            )

        if self.current_section == "personal_history":
            targets = [
                target
                for target in PERSONAL_GROUPS
                if not self.target_answered(
                    target
                )
            ]
            return self._prioritize_pending(
                targets,
                pending,
            )

        if self.current_section == "review_of_systems":
            targets = [
                target
                for target in ROS_TARGETS
                if not self.target_answered(
                    target
                )
            ]
            return self._prioritize_pending(
                targets,
                pending,
            )

        return self._prioritize_pending(
            [
                target
                for target in AYUSH_REQUIRED
                if not self.target_answered(
                    target
                )
            ],
            pending,
        )

    @staticmethod
    def _split_targets(
        target: str | None,
    ) -> list[str]:
        if not target:
            return []

        raw = (
            target[7:]
            if target.startswith("bundle:")
            else target
        )

        return [
            item.strip()
            for item in re.split(
                r"[,|;/]+|\band\b|और|तथा|aur",
                raw,
                flags=re.IGNORECASE,
            )
            if item.strip()
        ]

    def section_question_count(
        self,
        section: str | None = None,
    ) -> int:
        current = normalize_section(
            section
            or self.current_section
        )

        count = 0

        for target in self.target_history:
            targets = self._split_targets(
                target
            )

            sections = {
                FIELD_PRIMARY_SECTION.get(
                    item
                )
                for item in targets
            }

            if current in sections:
                count += 1

        return count

    def section_budget_reached(
        self,
        section: str | None = None,
    ) -> bool:
        current = normalize_section(
            section
            or self.current_section
        )

        budget = SECTION_QUESTION_BUDGETS.get(
            current
        )

        if budget is None:
            return False

        return (
            self.section_question_count(
                current
            )
            >= budget
        )

    def hpi_ready_for_closure(self) -> bool:
        if not self.target_answered(
            "chief_complaint"
        ):
            return False

        covered = sum(
            any(
                self.target_answered(
                    field
                )
                for field in group
            )
            for group in HPI_CORE_GROUPS
        )

        return (
            covered >= 6
            and self.target_answered(
                "associated_symptoms"
            )
        )

    def past_ready_for_closure(self) -> bool:
        return all(
            self.target_answered(
                field
            )
            for field in (
                *PAST_REQUIRED,
                "immunizations",
            )
        )

    def drug_ready_for_closure(self) -> bool:
        return all(
            self.target_answered(
                field
            )
            for field in DRUG_REQUIRED
        )

    def family_ready_for_closure(self) -> bool:
        return self.target_answered(
            "family_history"
        )

    def personal_ready_for_closure(self) -> bool:
        return (
            sum(
                self.target_answered(
                    field
                )
                for field in PERSONAL_GROUPS
            )
            >= 5
        )

    def ros_ready_for_closure(self) -> bool:
        return (
            sum(
                self.target_answered(
                    field
                )
                for field in ROS_TARGETS
            )
            >= 6
        )

    def ayush_ready_for_closure(self) -> bool:
        return (
            sum(
                self.target_answered(
                    field
                )
                for field in AYUSH_REQUIRED
            )
            >= len(
                AYUSH_REQUIRED
            )
        )

    def section_naturally_ready(
        self,
        section: str | None = None,
    ) -> bool:
        current = normalize_section(
            section
            or self.current_section
        )

        return {
            "hpi": self.hpi_ready_for_closure(),
            "past_history": self.past_ready_for_closure(),
            "drug_allergy": self.drug_ready_for_closure(),
            "family_history": self.family_ready_for_closure(),
            "personal_history": self.personal_ready_for_closure(),
            "review_of_systems": self.ros_ready_for_closure(),
            AYUSH_SECTION: self.ayush_ready_for_closure(),
        }.get(
            current,
            False,
        )

    def section_summary(
        self,
    ) -> dict[str, dict[str, Any]]:
        return {
            section: {
                "completed": (
                    section
                    in self.completed_sections
                ),
                "facts": [
                    {
                        "field": fact.get(
                            "field"
                        ),
                        "value": fact.get(
                            "value"
                        ),
                        "negative": bool(
                            fact.get(
                                "negative"
                            )
                        ),
                    }
                    for fact in self.section_facts(
                        section
                    )
                ],
            }
            for section in ALL_SECTIONS
        }

    def render_section(
        self,
        section: str,
    ) -> str | None:
        facts = self.section_facts(
            section
        )

        if not facts:
            return None

        lines: list[str] = []
        seen: set[str] = set()

        for fact in facts:
            field = str(
                fact.get(
                    "field"
                )
                or "detail"
            ).replace(
                "_",
                " ",
            )

            value = (
                "No / not reported"
                if fact.get(
                    "negative"
                )
                else (
                    ", ".join(
                        str(item)
                        for item in fact.get(
                            "value"
                        )
                    )
                    if isinstance(
                        fact.get(
                            "value"
                        ),
                        list,
                    )
                    else str(
                        fact.get(
                            "value"
                        )
                    )
                )
            )

            line = (
                f"{field}: {value}"
            )

            if line not in seen:
                lines.append(
                    line
                )
                seen.add(line)

        return "; ".join(
            lines
        )
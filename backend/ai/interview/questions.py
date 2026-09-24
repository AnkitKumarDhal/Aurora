from __future__ import annotations

from dataclasses import dataclass

from backend.ai.interview.state import InterviewState, SECTION_ORDER


@dataclass(frozen=True)
class QuestionSpec:
    field: str
    en: str
    hi: str


TOPIC_KEYWORDS = {
    "headache": ("headache", "migraine", "head pain", "सिरदर्द", "सिर में दर्द"),
    "chest_pain": ("chest pain", "chest pressure", "chest discomfort", "सीने में दर्द", "सीने में दबाव"),
    "respiratory": ("cough", "breathless", "shortness of breath", "difficulty breathing", "खांसी", "सांस फूलना", "साँस फूलना"),
    "gastrointestinal": ("constipation", "constipated", "hard stool", "diarrhea", "loose stools", "stomach pain", "abdominal pain", "vomiting", "nausea", "कब्ज", "दस्त", "पेट में दर्द", "उल्टी", "मतली"),
    "skin": ("rash", "itching", "skin problem", "दाने", "चकत्ते", "खुजली"),
    "urinary": ("urine", "urination", "burning while urinating", "painful urination", "पेशाब", "मूत्र", "पेशाब में जलन"),
    "musculoskeletal": ("back pain", "joint pain", "muscle pain", "neck pain", "कमर दर्द", "जोड़ों का दर्द"),
    "neurological": ("numbness", "tingling", "weakness", "सुन्नपन", "झनझनाहट", "कमजोरी", "कमज़ोरी"),
}

GENERIC_HPI = (
    QuestionSpec("onset", "When did this problem start?",
                 "यह समस्या कब शुरू हुई?"),
    QuestionSpec("duration", "How long has it been present?",
                 "यह समस्या कितने समय से है?"),
    QuestionSpec("site", "Where exactly do you feel it?",
                 "आपको यह समस्या शरीर में ठीक कहाँ महसूस होती है?"),
    QuestionSpec("severity", "On a scale of 0 to 10, how severe is it?",
                 "0 से 10 के पैमाने पर यह समस्या कितनी गंभीर है?"),
    QuestionSpec("character", "What does it feel like?",
                 "यह कैसा महसूस होता है?"),
    QuestionSpec("timing", "Is it constant, or does it come and go?",
                 "क्या यह लगातार रहता है या बीच-बीच में आता-जाता है?"),
    QuestionSpec("aggravating_factors", "What makes it worse?",
                 "किस वजह से यह समस्या बढ़ जाती है?"),
    QuestionSpec("relieving_factors", "What makes it better?",
                 "किस चीज़ से यह समस्या कम होती है?"),
    QuestionSpec("radiation", "Does it spread anywhere else?",
                 "क्या यह समस्या शरीर के किसी और हिस्से तक फैलती है?"),
    QuestionSpec("associated_symptoms", "What other symptoms do you notice with it?",
                 "इसके साथ आपको और कौन से लक्षण महसूस होते हैं?"),
    QuestionSpec("previous_episodes", "Have you had this problem before?",
                 "क्या आपको यह समस्या पहले भी हुई है?"),
    QuestionSpec("prior_treatment", "Have you tried any medicine or other treatment for it?",
                 "क्या आपने इसके लिए कोई दवा या दूसरा इलाज आज़माया है?"),
    QuestionSpec("response_to_treatment", "Did that treatment help?",
                 "क्या उस इलाज से आपको फायदा हुआ?"),
    QuestionSpec("prior_investigations", "Have you had any tests or scans for this problem?",
                 "क्या इस समस्या के लिए कोई जाँच या स्कैन हुआ है?"),
    QuestionSpec("impact_on_daily_life", "Is this affecting your sleep, work, eating, or normal activities?",
                 "क्या यह आपकी नींद, काम, खाने या सामान्य गतिविधियों को प्रभावित कर रहा है?"),
)

TOPIC_HPI = {
    "gastrointestinal": (
        QuestionSpec("bowel_frequency", "How often are you passing stool?",
                     "आपको कितनी बार मल त्याग हो रहा है?"),
        QuestionSpec("stool_consistency", "What is the stool like, for example hard, normal, loose, or watery?",
                     "मल कैसा है, जैसे सख्त, सामान्य, ढीला या पानी जैसा?"),
        QuestionSpec("straining", "Do you have to strain to pass stool?",
                     "क्या मल त्याग करते समय आपको जोर लगाना पड़ता है?"),
        QuestionSpec("blood_in_stool", "Have you seen any blood in or on the stool?",
                     "क्या आपने मल में या मल पर खून देखा है?"),
        QuestionSpec("abdominal_distension", "Do you have bloating or swelling of the abdomen?",
                     "क्या पेट में फूलना या सूजन होती है?"),
    ),
    "chest_pain": (
        QuestionSpec("character", "What does the chest discomfort feel like?",
                     "सीने की तकलीफ़ कैसी महसूस होती है?"),
        QuestionSpec("radiation", "Does the chest discomfort spread to your arm, jaw, neck, back, or anywhere else?",
                     "क्या सीने की तकलीफ़ हाथ, जबड़े, गर्दन, पीठ या किसी और जगह तक फैलती है?"),
        QuestionSpec("aggravating_factors", "Does it happen with walking, exercise, or at rest?",
                     "क्या यह चलने, व्यायाम करने या आराम के समय होता है?"),
        QuestionSpec("associated_symptoms", "Do you also have breathlessness, sweating, dizziness, or nausea with it?",
                     "क्या इसके साथ साँस फूलना, पसीना, चक्कर या मतली भी होती है?"),
    ),
    "headache": (
        QuestionSpec("site", "Where on your head is the pain?",
                     "सिर में दर्द कहाँ होता है?"),
        QuestionSpec("character", "What does the headache feel like?",
                     "सिर का दर्द कैसा महसूस होता है?"),
        QuestionSpec("nausea_vomiting", "Do you have nausea or vomiting with the headache?",
                     "क्या सिरदर्द के साथ मतली या उल्टी होती है?"),
        QuestionSpec("vision_or_neuro", "Have you noticed any vision change, numbness, weakness, or trouble speaking?",
                     "क्या आपको दृष्टि में बदलाव, सुन्नपन, कमजोरी या बोलने में परेशानी हुई है?"),
    ),
    "respiratory": (
        QuestionSpec("cough", "Do you have a cough?", "क्या आपको खाँसी है?"),
        QuestionSpec("breathing_difficulty", "Do you feel short of breath or have difficulty breathing?",
                     "क्या आपको साँस फूलती है या साँस लेने में कठिनाई होती है?"),
        QuestionSpec("fever", "Have you had fever with this problem?",
                     "क्या इस समस्या के साथ बुखार भी हुआ है?"),
        QuestionSpec("associated_symptoms", "Do you have any other breathing or chest symptoms?",
                     "क्या साँस या सीने से जुड़े कोई और लक्षण हैं?"),
    ),
    "urinary": (
        QuestionSpec("urinary_frequency", "How often are you passing urine?",
                     "आपको कितनी बार पेशाब हो रहा है?"),
        QuestionSpec("urinary_burning", "Do you have burning or pain when passing urine?",
                     "क्या पेशाब करते समय जलन या दर्द होता है?"),
        QuestionSpec("urinary_blood", "Have you noticed any blood in your urine?",
                     "क्या आपने पेशाब में खून देखा है?"),
        QuestionSpec("associated_symptoms", "Do you have fever, lower abdominal pain, or back pain with it?",
                     "क्या इसके साथ बुखार, पेट के निचले हिस्से में दर्द या कमर दर्द है?"),
    ),
    "skin": (
        QuestionSpec("site", "Where on your body is the skin problem?",
                     "शरीर में त्वचा की समस्या कहाँ है?"),
        QuestionSpec("character", "What does the rash or skin change look or feel like?",
                     "दाने या त्वचा में बदलाव कैसा दिखता या महसूस होता है?"),
        QuestionSpec("associated_symptoms", "Is there itching, pain, fever, or any discharge with it?",
                     "क्या इसके साथ खुजली, दर्द, बुखार या कोई स्राव है?"),
    ),
    "musculoskeletal": (
        QuestionSpec("site", "Where exactly is the pain?",
                     "दर्द ठीक कहाँ है?"),
        QuestionSpec("laterality", "Is it on one side or both sides?",
                     "क्या यह एक तरफ है या दोनों तरफ?"),
        QuestionSpec("character", "What does the pain feel like?",
                     "दर्द कैसा महसूस होता है?"),
        QuestionSpec("aggravating_factors", "What movements or activities make it worse?",
                     "कौन सी हरकत या गतिविधि से दर्द बढ़ता है?"),
    ),
    "neurological": (
        QuestionSpec("site", "Where do you feel the weakness, numbness, or other symptom?",
                     "कमजोरी, सुन्नपन या दूसरा लक्षण आपको कहाँ महसूस होता है?"),
        QuestionSpec("vision_or_neuro", "Have you had any vision change, trouble speaking, or loss of balance?",
                     "क्या दृष्टि में बदलाव, बोलने में परेशानी या संतुलन बिगड़ने की समस्या हुई है?"),
        QuestionSpec("associated_symptoms", "Have you noticed any other new neurological symptoms?",
                     "क्या आपको कोई और नया तंत्रिका संबंधी लक्षण महसूस हुआ है?"),
    ),
}

SECTION_QUESTIONS = {
    "past_history": (
        QuestionSpec("past_medical_history", "Have you ever been diagnosed with any important medical condition?",
                     "क्या आपको पहले कभी कोई महत्वपूर्ण बीमारी बताई गई है?"),
        QuestionSpec("past_surgical_history", "Have you ever had any major surgery or operation?",
                     "क्या आपकी कभी कोई बड़ी सर्जरी या ऑपरेशन हुआ है?"),
        QuestionSpec("hospitalizations", "Have you ever been admitted to a hospital for any reason?",
                     "क्या आपको कभी किसी कारण से अस्पताल में भर्ती होना पड़ा है?"),
    ),
    "drug_allergy": (
        QuestionSpec("medications", "Are you taking any regular medicines or supplements?",
                     "क्या आप कोई नियमित दवा या सप्लीमेंट लेते हैं?"),
        QuestionSpec("allergies", "Do you have any medicine or food allergies?",
                     "क्या आपको किसी दवा या खाने से एलर्जी है?"),
        QuestionSpec("adverse_drug_reactions", "Have you ever had a bad reaction to a medicine?",
                     "क्या किसी दवा से आपको कभी कोई खराब प्रतिक्रिया हुई है?"),
    ),
    "family_history": (QuestionSpec("family_history", "Is there any important medical condition that runs in your family?", "क्या आपके परिवार में कोई महत्वपूर्ण बीमारी चलती है?"),),
    "personal_history": (
        QuestionSpec("occupation", "What kind of work or study do you do?",
                     "आप क्या काम या पढ़ाई करते हैं?"),
        QuestionSpec("smoking", "Do you smoke or use tobacco?",
                     "क्या आप धूम्रपान या तंबाकू का उपयोग करते हैं?"),
        QuestionSpec("alcohol", "Do you drink alcohol?",
                     "क्या आप शराब का सेवन करते हैं?"),
        QuestionSpec("diet", "How would you describe your usual diet?",
                     "आप अपने सामान्य भोजन को कैसे बताएँगे?"),
        QuestionSpec("sleep", "How is your usual sleep?",
                     "आपकी सामान्य नींद कैसी रहती है?"),
        QuestionSpec("physical_activity", "How physically active are you in a usual day?",
                     "एक सामान्य दिन में आप कितने शारीरिक रूप से सक्रिय रहते हैं?"),
    ),
    "review_of_systems": (QuestionSpec("review_of_systems", "Apart from this problem, have you noticed any other new symptoms or changes in your health?", "इस समस्या के अलावा क्या आपने कोई और नए लक्षण या अपने स्वास्थ्य में कोई बदलाव देखा है?"),),
    "ayush": (
        QuestionSpec("ayush_prakriti", "Do you know your Ayurvedic Prakriti or constitution? If you have been told it before, please share it; otherwise you can say you do not know.",
                     "क्या आपको अपनी आयुर्वेदिक प्रकृति या शरीर की संरचना के बारे में जानकारी है? यदि पहले किसी ने बताया है तो बताइए, नहीं पता हो तो आप कह सकते हैं कि आपको जानकारी नहीं है।"),
        QuestionSpec("ayush_vikriti", "Has an AYUSH practitioner ever told you about a current Vikriti or imbalance?",
                     "क्या किसी आयुष चिकित्सक ने आपको वर्तमान विकृति या असंतुलन के बारे में कभी बताया है?"),
        QuestionSpec("ayush_sara", "If you know your Ayurvedic Sara, or tissue quality, what were you told?",
                     "यदि आपको अपनी आयुर्वेदिक सार या धातु की गुणवत्ता के बारे में बताया गया है, तो क्या बताया गया था?"),
        QuestionSpec("ayush_samhanana", "If you know your Samhanana or body compactness, what were you told?",
                     "यदि आपको अपने संहनन या शरीर की बनावट के बारे में बताया गया है, तो क्या बताया गया था?"),
        QuestionSpec("ayush_pramana", "If you know your Pramana or body proportions, what information were you given?",
                     "यदि आपको अपने प्रमाण या शरीर के अनुपात के बारे में बताया गया है, तो क्या जानकारी दी गई थी?"),
        QuestionSpec("ayush_satmya", "If an AYUSH practitioner has described your Satmya or suitability or tolerance to foods or routines, what did they tell you?",
                     "यदि किसी आयुष चिकित्सक ने आपके सात्म्य या किन खाद्य पदार्थों और दिनचर्याओं के अनुकूल होने के बारे में बताया है, तो क्या बताया था?"),
        QuestionSpec("ayush_satva", "If you know your Satva or mental disposition as described in an AYUSH consultation, what were you told?",
                     "यदि आयुष परामर्श में आपके सत्त्व या मानसिक प्रवृत्ति के बारे में कुछ बताया गया है, तो क्या बताया था?"),
        QuestionSpec("ayush_ahara_shakti", "What were you told about your Ahara Shakti, or your usual capacity to take food?",
                     "आपकी आहार शक्ति या सामान्य रूप से भोजन ग्रहण करने की क्षमता के बारे में क्या बताया गया है?"),
        QuestionSpec("ayush_vyayama_shakti", "What were you told about your Vyayama Shakti, or your usual exercise capacity?",
                     "आपकी व्यायाम शक्ति या सामान्य व्यायाम क्षमता के बारे में क्या बताया गया है?"),
        QuestionSpec("ayush_vaya", "What age-related or Vaya information is relevant in your AYUSH history?",
                     "आपके आयुष इतिहास में वय या उम्र से जुड़ी कौन सी जानकारी प्रासंगिक है?"),
        QuestionSpec("ayush_ahara_vihara", "Are there any important AYUSH details about your diet, daily routine, sleep, activity, or habits?",
                     "आपके भोजन, दैनिक दिनचर्या, नींद, गतिविधि या आदतों से जुड़ी कोई महत्वपूर्ण आयुष जानकारी है?"),
        QuestionSpec("ayush_agni", "If you know your Agni or digestive pattern from an AYUSH consultation, what were you told?",
                     "यदि आयुष परामर्श में आपकी अग्नि या पाचन प्रकृति के बारे में बताया गया है, तो क्या बताया गया था?"),
        QuestionSpec("ayush_koshta", "If you know your Koshtha or bowel pattern as described in AYUSH, what were you told?",
                     "यदि आयुष में आपके कोष्ठ या मल त्याग के पैटर्न के बारे में बताया गया है, तो क्या बताया गया था?"),
        QuestionSpec("ayush_nidana", "Were any AYUSH-specific causes or Nidana for your present problem explained to you by a practitioner?",
                     "क्या किसी आयुष चिकित्सक ने आपकी वर्तमान समस्या के लिए कोई आयुष-विशिष्ट कारण या निदान के बारे में बताया है?"),
        QuestionSpec("ayush_samprapti", "Were you given any explanation of how the present problem developed according to your AYUSH consultation?",
                     "क्या आपके आयुष परामर्श में वर्तमान समस्या के विकसित होने की प्रक्रिया या सम्प्राप्ति के बारे में कुछ समझाया गया था?"),
    ),
}

VALID_TOPICS = set(TOPIC_KEYWORDS) | {"general"}

TOPIC_REQUIRED = {
    "general": {"onset", "severity", "associated_symptoms"},
    "headache": {"onset", "severity", "site", "associated_symptoms"},
    "chest_pain": {"onset", "severity", "character", "radiation", "associated_symptoms"},
    "respiratory": {"onset", "cough", "breathing_difficulty", "associated_symptoms"},
    "gastrointestinal": {"onset", "bowel_frequency", "stool_consistency", "straining", "blood_in_stool", "associated_symptoms"},
    "skin": {"onset", "site", "character", "associated_symptoms"},
    "urinary": {"onset", "urinary_frequency", "urinary_burning", "urinary_blood"},
    "musculoskeletal": {"onset", "site", "severity", "character"},
    "neurological": {"onset", "site", "severity", "vision_or_neuro"},
}


def detect_topic(text: str) -> str | None:
    normalized = text.strip().lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return topic
    return None


def topic_questions(topic: str) -> tuple[QuestionSpec, ...]:
    return TOPIC_HPI.get(topic, ())


def section_questions(section: str, topic: str) -> tuple[QuestionSpec, ...]:
    if section != "hpi":
        return SECTION_QUESTIONS.get(section, ())
    result: list[QuestionSpec] = []
    seen: set[str] = set()
    topic_specs = list(topic_questions(topic))
    topic_by_field = {item.field: item for item in topic_specs}
    generic = {item.field: item for item in GENERIC_HPI}
    required = TOPIC_REQUIRED.get(topic, TOPIC_REQUIRED["general"])
    required_topic = [
        item.field for item in topic_specs if item.field in required]
    optional_topic = [
        item.field for item in topic_specs if item.field not in required]
    required_generic = [
        item.field for item in GENERIC_HPI if item.field in required]
    optional_generic = [
        item.field for item in GENERIC_HPI if item.field not in required and item.field not in topic_by_field and item.field not in {"onset", "duration"}]
    order = ["onset", "duration"] + required_topic + \
        required_generic + optional_topic + optional_generic
    for field in order:
        item = topic_by_field.get(field) or generic.get(field)
        if item and field not in seen:
            result.append(item)
            seen.add(field)
    return tuple(result)


def section_complete(state: InterviewState, section: str) -> bool:
    normalized = section
    if normalized in state.completed_sections:
        return True
    if normalized in state.stopped_sections:
        if normalized != "hpi":
            return bool(state.section_fields(normalized))
        known = state.known_fields()
        answered_hpi = len([field for field in state.section_fields(
            "hpi") if field != "chief_complaint"])
        return bool(known.get("chief_complaint")) and answered_hpi >= 3
    if normalized == "hpi":
        known = state.known_fields()
        required = TOPIC_REQUIRED.get(state.topic, TOPIC_REQUIRED["general"])
        missing = required - set(known)
        if "onset" in missing and ("onset" in known or "duration" in known):
            missing.remove("onset")
        return bool(known.get("chief_complaint")) and not missing
    required_by_section = {
        "past_history": {"past_medical_history", "past_surgical_history", "hospitalizations"},
        "drug_allergy": {"medications", "allergies", "adverse_drug_reactions"},
        "family_history": {"family_history"},
        "personal_history": {"occupation", "smoking", "alcohol", "diet", "sleep", "physical_activity"},
        "review_of_systems": {"review_of_systems"},
        "ayush": {
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
        },
    }
    required = required_by_section.get(normalized, set())
    known = state.known_fields()
    return required.issubset(known)


def choose_question(state: InterviewState, language: str, suggested_field: str | None = None) -> QuestionSpec | None:
    specs = section_questions(state.current_section, state.topic)
    if suggested_field:
        for item in specs:
            if item.field == suggested_field and not state.answered(item.field):
                return item
    for item in specs:
        if item.field in {"onset", "duration"} and (state.answered("onset") or state.answered("duration")):
            continue
        if not state.answered(item.field):
            return item
    return None


def next_section(state: InterviewState) -> str | None:
    order = (*SECTION_ORDER, "ayush") if state.ayush_required else SECTION_ORDER
    for section in order:
        if section not in state.completed_sections:
            return section
    return None


def is_explicit_negative(text: str) -> bool:
    value = " ".join(text.strip().lower().split())
    return value in {"no", "none", "not applicable", "not relevant", "नहीं", "कोई नहीं"}


def is_stop_answer(text: str) -> bool:
    value = " ".join(text.strip().lower().split())
    return value in {"nothing else", "nothing more", "no more", "that's all", "thats all", "that is all", "कुछ नहीं", "और कुछ नहीं", "बस इतना ही"}
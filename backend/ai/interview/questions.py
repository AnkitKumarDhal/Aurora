from __future__ import annotations


QUESTIONS: dict[str, str] = {
    "chief_complaint": "What is the main problem you are having today?",
    "onset": "When did this problem start?",
    "site": "Where exactly do you feel it?",
    "severity": "How severe is it on a scale of 0 to 10?",
    "character": "What does it feel like — for example, pressure, burning, throbbing, stabbing, or something else?",
    "timing": "Is it constant, or does it come and go?",
    "aggravating_factors": "What makes it worse?",
    "relieving_factors": "What makes it better?",
    "radiation": "Does the discomfort spread anywhere else?",
    "associated_symptoms": "What other symptoms have you noticed with it?",
    "breathing_difficulty": "Have you had any difficulty breathing or shortness of breath?",
    "nausea_vomiting": "Have you had nausea or vomiting?",
    "vision_or_neuro": "Have you had any vision changes, weakness, numbness, confusion, or other unusual neurological symptoms?",
    "cough": "Have you had a cough?",
    "wheeze": "Have you noticed wheezing or a whistling sound when breathing?",
    "location": "Where in your abdomen or digestive system is the problem?",
    "bowel_changes": "Have you noticed any change in your bowel movements?",
    "appearance": "What does the affected skin area look like?",
    "itch_or_pain": "Is the area itchy, painful, or both?",
    "spread": "Has the affected area spread or changed size?",
    "urinary_frequency": "Have you been urinating more or less often than usual?",
    "urinary_burning": "Do you have burning or pain while urinating?",
    "urinary_blood": "Have you noticed any blood in your urine?",
    "fever": "Have you had a fever?",
    "fatigue": "Have you felt unusually tired?",
    "weight_change": "Have you had any unexpected weight change?",
}


QUESTIONS_HI: dict[str, str] = {
    "chief_complaint": "आज आपको मुख्य समस्या क्या हो रही है?",
    "onset": "यह समस्या कब शुरू हुई?",
    "site": "आपको यह समस्या शरीर में ठीक कहाँ महसूस होती है?",
    "severity": "0 से 10 के पैमाने पर यह समस्या कितनी गंभीर है?",
    "character": "यह कैसा महसूस होता है — जैसे दबाव, जलन, धड़कना, चुभना या कुछ और?",
    "timing": "क्या यह लगातार रहता है या बीच-बीच में होता है?",
    "aggravating_factors": "किस चीज़ से यह समस्या बढ़ जाती है?",
    "relieving_factors": "किस चीज़ से यह समस्या कम होती है?",
    "radiation": "क्या यह तकलीफ़ शरीर के किसी और हिस्से तक फैलती है?",
    "associated_symptoms": "इसके साथ आपको और कौन से लक्षण हुए हैं?",
    "breathing_difficulty": "क्या आपको सांस लेने में दिक्कत या सांस फूलने की समस्या हुई है?",
    "nausea_vomiting": "क्या आपको मतली या उल्टी हुई है?",
    "vision_or_neuro": "क्या आपकी दृष्टि में बदलाव, कमजोरी, सुन्नपन, भ्रम या कोई और असामान्य न्यूरोलॉजिकल लक्षण हुआ है?",
    "cough": "क्या आपको खांसी हुई है?",
    "wheeze": "क्या सांस लेते समय सीटी जैसी आवाज़ या घरघराहट होती है?",
    "location": "आपके पेट या पाचन तंत्र में यह समस्या कहाँ है?",
    "bowel_changes": "क्या आपके मल त्याग में कोई बदलाव आया है?",
    "appearance": "प्रभावित त्वचा का हिस्सा कैसा दिखाई देता है?",
    "itch_or_pain": "क्या उस जगह पर खुजली, दर्द या दोनों हैं?",
    "spread": "क्या प्रभावित जगह फैली है या उसका आकार बदला है?",
    "urinary_frequency": "क्या आप सामान्य से ज्यादा या कम बार पेशाब कर रहे हैं?",
    "urinary_burning": "क्या पेशाब करते समय जलन या दर्द होता है?",
    "urinary_blood": "क्या आपने पेशाब में खून देखा है?",
    "fever": "क्या आपको बुखार हुआ है?",
    "fatigue": "क्या आपको सामान्य से बहुत ज्यादा थकान महसूस हुई है?",
    "weight_change": "क्या आपके वजन में बिना किसी खास कारण के बदलाव हुआ है?",
}


QUESTION_TO_FIELD = {
    question: field
    for field, question in QUESTIONS.items()
}


QUESTION_HI_TO_FIELD = {
    question: field
    for field, question in QUESTIONS_HI.items()
}


BOOLEAN_FIELDS = {
    "associated_symptoms",
    "breathing_difficulty",
    "nausea_vomiting",
    "vision_or_neuro",
    "cough",
    "wheeze",
    "bowel_changes",
    "urinary_frequency",
    "urinary_burning",
    "urinary_blood",
    "fever",
    "fatigue",
    "weight_change",
}


def question_for(field: str, language: str | None = "en") -> str:
    questions = QUESTIONS_HI if language == "hi" else QUESTIONS

    return questions.get(
        field,
        (
            "इस लक्षण के बारे में डॉक्टर को बताने लायक और कुछ महत्वपूर्ण है?"
            if language == "hi"
            else "Is there anything else important about this symptom that you think the doctor should know?"
        ),
    )


def field_for_question(question: str | None) -> str | None:
    if not question:
        return None

    normalized = question.strip()

    return (
        QUESTION_TO_FIELD.get(normalized)
        or QUESTION_HI_TO_FIELD.get(normalized)
    )


def is_boolean_field(field: str | None) -> bool:
    return field in BOOLEAN_FIELDS

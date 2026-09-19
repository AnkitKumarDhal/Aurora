from backend.ai.question_planner import QuestionPlanner


class FakeProvider:
    def __init__(
        self,
        result,
    ):
        self.result = result

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ):
        return self.result


class FakeSession:
    def __init__(self):
        self.patient_history = {
            "chief_complaint": "chest pain",
        }
        self.complaint_categories = [
            "pain",
            "general",
        ]
        self.red_flags = []
        self.contradictions = []
        self.raw_responses = []
        self.question_queue = [
            {
                "field": "onset",
                "question": "When did the problem start?",
            },
            {
                "field": "site",
                "question": "Where exactly do you feel the pain?",
            },
            {
                "field": "severity",
                "question": "How severe is the pain from 0 to 10?",
            },
        ]

        self._answered = {
            "onset",
        }

    def _field_has_value(
        self,
        field: str,
    ) -> bool:
        return field in self._answered


def test_planner_accepts_valid_llm_decision():
    provider = FakeProvider(
        {
            "action": "ASK",
            "next_field": "severity",
            "question": (
                "How severe is the chest pain when it happens, "
                "from 0 to 10?"
            ),
            "reason": "Severity has not been established.",
            "confidence": 0.94,
            "answer_mode": "scale_0_10",
        }
    )

    planner = QuestionPlanner(
        provider,
    )

    decision = planner.plan(
        session=FakeSession(),
        language="en",
        previous_turns=[],
    )

    assert decision is not None
    assert decision.action == "ASK"
    assert decision.next_field == "severity"
    assert decision.answer_mode == "scale_0_10"


def test_planner_rejects_unknown_field():
    provider = FakeProvider(
        {
            "action": "ASK",
            "next_field": "diagnosis",
            "question": "What diagnosis do you think you have?",
            "reason": "invalid",
            "confidence": 0.95,
            "answer_mode": "free_text",
        }
    )

    planner = QuestionPlanner(
        provider,
    )

    decision = planner.plan(
        session=FakeSession(),
        language="en",
        previous_turns=[],
    )

    assert decision is None


def test_planner_rejects_premature_completion():
    provider = FakeProvider(
        {
            "action": "COMPLETE",
            "next_field": None,
            "question": None,
            "reason": "Done.",
            "confidence": 0.99,
            "answer_mode": "free_text",
        }
    )

    planner = QuestionPlanner(
        provider,
    )

    decision = planner.plan(
        session=FakeSession(),
        language="en",
        previous_turns=[],
    )

    assert decision is None


def test_planner_falls_back_to_first_missing_field():
    planner = QuestionPlanner(
        FakeProvider(None),
    )

    fallback = planner.deterministic_fallback(
        session=FakeSession(),
    )

    assert fallback == (
        "site",
        "Where exactly do you feel the pain?",
    )

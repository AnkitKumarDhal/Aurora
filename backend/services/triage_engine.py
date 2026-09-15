from dataclasses import dataclass
from typing import Any

from backend.domain.enums import UrgencyLevel


@dataclass(frozen=True)
class TriageAssessment:
    urgency_level: UrgencyLevel
    priority_score: int
    red_flags_present: bool


class TriageEngine:
    def assess(self, signals: list[dict[str, Any]]) -> TriageAssessment:
        normalized = {
            str(signal.get("name", "")).strip().lower(): signal.get("value")
            for signal in signals
        }

        if self._has_critical_red_flag(normalized):
            return TriageAssessment(
                urgency_level=UrgencyLevel.LEVEL_5,
                priority_score=100,
                red_flags_present=True,
            )

        urgency_level = self._calculate_urgency(normalized)
        priority_score = self._calculate_priority(urgency_level, normalized)

        return TriageAssessment(
            urgency_level=urgency_level,
            priority_score=priority_score,
            red_flags_present=False,
        )

    @staticmethod
    def _has_critical_red_flag(signals: dict[str, Any]) -> bool:
        critical_flags = (
            "loss_of_consciousness",
            "severe_breathing_difficulty",
            "active_severe_bleeding",
            "stroke_symptoms",
            "severe_chest_pain",
            "suicidal_intent",
        )

        return any(signals.get(flag) is True for flag in critical_flags)

    @staticmethod
    def _calculate_urgency(signals: dict[str, Any]) -> UrgencyLevel:
        if signals.get("severe_pain") is True:
            return UrgencyLevel.LEVEL_4

        if signals.get("moderate_pain") is True:
            return UrgencyLevel.LEVEL_3

        if signals.get("persistent_symptoms") is True:
            return UrgencyLevel.LEVEL_2

        return UrgencyLevel.LEVEL_1

    @staticmethod
    def _calculate_priority(urgency_level: UrgencyLevel, signals: dict[str, Any]) -> int:
        base_scores = {
            UrgencyLevel.LEVEL_1: 20,
            UrgencyLevel.LEVEL_2: 35,
            UrgencyLevel.LEVEL_3: 55,
            UrgencyLevel.LEVEL_4: 75,
            UrgencyLevel.LEVEL_5: 100,
        }

        score = base_scores[urgency_level]

        if signals.get("elderly_patient") is True:
            score += 5

        if signals.get("pregnancy") is True:
            score += 5

        return min(score, 99)

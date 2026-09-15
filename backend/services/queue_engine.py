from datetime import datetime, timezone

from backend.domain.enums import QueueStatus
from backend.domain.queue import QueueEntry


class QueueEngine:
    WAITING_TIME_BONUS_PER_MINUTE = 0.5
    MAX_WAITING_TIME_BONUS = 30.0

    def effective_priority(self, entry: QueueEntry, now: datetime | None = None) -> float:
        if entry.priority_score is None:
            return 0.0

        if entry.queued_at is None:
            return float(entry.priority_score)

        current_time = now or datetime.now(timezone.utc)

        if current_time < entry.queued_at:
            return float(entry.priority_score)

        waited_minutes = (
            current_time - entry.queued_at
        ).total_seconds() / 60.0

        waiting_bonus = min(
            waited_minutes * self.WAITING_TIME_BONUS_PER_MINUTE,
            self.MAX_WAITING_TIME_BONUS,
        )

        return entry.priority_score + waiting_bonus

    def sort_entries(
        self,
        entries: list[QueueEntry],
        now: datetime | None = None,
    ) -> list[QueueEntry]:
        waiting_entries = [
            entry
            for entry in entries
            if entry.status == QueueStatus.WAITING
        ]

        return sorted(
            waiting_entries,
            key=lambda entry: (
                -self.effective_priority(entry, now),
                entry.queued_at or datetime.max.replace(tzinfo=timezone.utc),
                entry.queue_entry_id,
            ),
        )

    def assign_positions(
        self,
        entries: list[QueueEntry],
        now: datetime | None = None,
    ) -> list[QueueEntry]:
        ordered_entries = self.sort_entries(entries, now)

        for position, entry in enumerate(ordered_entries, start=1):
            entry.position = position

        return ordered_entries

    def next_patient(
        self,
        entries: list[QueueEntry],
        now: datetime | None = None,
    ) -> QueueEntry | None:
        ordered_entries = self.sort_entries(entries, now)

        if not ordered_entries:
            return None

        return ordered_entries[0]

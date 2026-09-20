from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class EventType(str, Enum):
    QUEUE_UPDATED = "QUEUE_UPDATED"
    ASSIGNMENT_UPDATED = "ASSIGNMENT_UPDATED"
    PROMOTION_UPDATED = "PROMOTION_UPDATED"


@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_id: str
    type: EventType
    department_id: str
    entity_id: str | None
    timestamp: datetime

    @classmethod
    def create(
        cls,
        event_type: EventType,
        department_id: str,
        entity_id: str | None = None,
    ) -> "DomainEvent":
        return cls(
            event_id=f"event_{uuid4().hex}",
            type=event_type,
            department_id=department_id,
            entity_id=entity_id,
            timestamp=datetime.now(timezone.utc),
        )

    def to_payload(self) -> dict[str, str | None]:
        return {
            "id": self.event_id,
            "type": self.type.value,
            "department_id": self.department_id,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat(),
        }

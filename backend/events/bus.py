import asyncio
from dataclasses import dataclass
from uuid import uuid4

from backend.events.types import DomainEvent, EventType


@dataclass(slots=True)
class _Subscriber:
    department_id: str
    queue: asyncio.Queue[DomainEvent]


class EventBus:
    MAX_QUEUE_SIZE = 100

    def __init__(self) -> None:
        self._subscribers: dict[str, _Subscriber] = {}

    def subscribe(
        self,
        department_id: str,
    ) -> tuple[str, asyncio.Queue[DomainEvent]]:
        subscriber_id = uuid4().hex
        subscriber = _Subscriber(
            department_id=department_id,
            queue=asyncio.Queue(maxsize=self.MAX_QUEUE_SIZE),
        )
        self._subscribers[subscriber_id] = subscriber
        return subscriber_id, subscriber.queue

    def unsubscribe(self, subscriber_id: str) -> None:
        self._subscribers.pop(subscriber_id, None)

    async def publish(self, event: DomainEvent) -> None:
        subscribers = tuple(self._subscribers.items())

        for subscriber_id, subscriber in subscribers:
            if subscriber.department_id != event.department_id:
                continue

            if subscriber.queue.full():
                try:
                    subscriber.queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

            try:
                subscriber.queue.put_nowait(event)
            except asyncio.QueueFull:
                self._subscribers.pop(subscriber_id, None)

    async def emit(
        self,
        event_type: EventType,
        department_id: str,
        entity_id: str | None = None,
    ) -> DomainEvent:
        event = DomainEvent.create(
            event_type,
            department_id,
            entity_id,
        )
        await self.publish(event)
        return event


_event_bus = EventBus()


def get_event_bus() -> EventBus:
    return _event_bus

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from backend.api.dependencies import get_doctor_repository
from backend.auth.dependencies import require_roles
from backend.domain.enums import ActorRole
from backend.domain.user import User
from backend.events import EventBus, DomainEvent, get_event_bus


router = APIRouter(
    prefix="/events",
    tags=["events"],
)


def _sse_message(
    event: DomainEvent,
) -> str:
    return (
        f"id: {event.event_id}\n"
        f"event: {event.type.value}\n"
        f"data: {json.dumps(event.to_payload())}\n\n"
    )


async def _event_stream(
    request: Request,
    event_bus: EventBus,
    subscriber_id: str,
    queue: asyncio.Queue[DomainEvent],
) -> AsyncIterator[str]:
    try:
        yield ": connected\n\n"

        while True:
            if await request.is_disconnected():
                break

            try:
                event = await asyncio.wait_for(
                    queue.get(),
                    timeout=15,
                )
            except asyncio.TimeoutError:
                if await request.is_disconnected():
                    break

                yield ": heartbeat\n\n"
                continue

            yield _sse_message(event)
    except asyncio.CancelledError:
        raise
    finally:
        event_bus.unsubscribe(subscriber_id)


@router.get("/stream")
async def stream_events(
    request: Request,
    department_id: str = Query(..., min_length=1),
    current_user: User = Depends(
        require_roles(
            ActorRole.ADMIN,
            ActorRole.DOCTOR,
        ),
    ),
    doctor_repository=Depends(get_doctor_repository),
    event_bus: EventBus = Depends(get_event_bus),
) -> StreamingResponse:
    if current_user.role == ActorRole.DOCTOR:
        doctor = await doctor_repository.get_doctor(
            current_user.actor_id,
        )

        if doctor is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor account not found",
            )

        if department_id not in doctor.department_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor does not belong to this department",
            )

    subscriber_id, queue = event_bus.subscribe(
        department_id,
    )

    return StreamingResponse(
        _event_stream(
            request,
            event_bus,
            subscriber_id,
            queue,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

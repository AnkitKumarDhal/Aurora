from fastapi import Depends, HTTPException, status
from backend.api.dependencies import get_assignment_repository, get_doctor_repository, get_queue_service
from backend.auth.dependencies import require_roles
from backend.domain.enums import ActorRole
from backend.domain.user import User
from backend.services.queue import QueueService


async def _ensure_department_access(department_id: str, current_user: User, doctor_repository) -> None:
    if current_user.role == ActorRole.ADMIN:
        return

    doctor = await doctor_repository.get_doctor(current_user.actor_id)

    if doctor is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Doctor profile not found")

    if department_id not in doctor.department_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Doctor does not have access to this department")


async def require_department_access(
    department_id: str,
    current_user: User = Depends(
        require_roles(ActorRole.ADMIN, ActorRole.DOCTOR)
    ),
    doctor_repository=Depends(get_doctor_repository)
) -> User:
    await _ensure_department_access(department_id, current_user, doctor_repository)
    return current_user


async def require_queue_entry_access(queue_entry_id: str, current_user: User = Depends(require_roles(ActorRole.ADMIN, ActorRole.DOCTOR)), queue_service: QueueService = Depends(get_queue_service), doctor_repository=Depends(get_doctor_repository)) -> User:
    entry = await queue_service.get_entry(queue_entry_id)

    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Queue entry not found")

    await _ensure_department_access(entry.department_id, current_user, doctor_repository)
    return current_user


async def require_assigned_doctor_access(session_id: str, current_user: User = Depends(require_roles(ActorRole.DOCTOR)), assignment_repository=Depends(get_assignment_repository)) -> User:
    assignment = await assignment_repository.get_session_assignment(session_id)

    if assignment is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No active doctor assignment for this session")

    if assignment.doctor_id != current_user.actor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Doctor is not assigned to this patient")

    return current_user

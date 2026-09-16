from fastapi import Depends, HTTPException, status
from backend.auth.dependencies import get_current_user
from backend.database.repositories.doctor import DoctorRepository
from backend.domain.enums import ActorRole
from backend.domain.user import User


async def require_queue_access(
    department_id: str,
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role == ActorRole.ADMIN:
        return current_user

    if current_user.role != ActorRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    doctor = await DoctorRepository().get_doctor(
        current_user.actor_id,
    )

    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor profile not found",
        )

    if department_id not in doctor.department_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor does not have access to this department",
        )

    return current_user

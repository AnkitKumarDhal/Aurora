import asyncio
from datetime import datetime, timedelta, timezone

from backend.database.repositories.assignment import (
    AssignmentRepository,
)
from backend.database.repositories.doctor import (
    DoctorRepository,
)
from backend.domain.enums import (
    PromotionStatus,
    QueueStatus,
)
from backend.domain.queue import QueueEntry
from backend.domain.promotion import (
    PromotionRequest,
)
from backend.services.promotion import (
    PromotionService,
)
from backend.services.queue import (
    QueueService,
)
from backend.services.reassignment import (
    ReassignmentService,
)


class PromotionWorkflowService:
    MIN_WAIT_SECONDS = 5 * 60
    MIN_WORKLOAD_ADVANTAGE = 2

    def __init__(
        self,
        promotion_service: PromotionService,
        queue_service: QueueService,
        reassignment_service: ReassignmentService,
        doctor_repository: DoctorRepository,
        assignment_repository: AssignmentRepository,
    ) -> None:
        self.promotion_service = (
            promotion_service
        )
        self.queue_service = (
            queue_service
        )
        self.reassignment_service = (
            reassignment_service
        )
        self.doctor_repository = (
            doctor_repository
        )
        self.assignment_repository = (
            assignment_repository
        )

        self._timeout_tasks: dict[
            str,
            asyncio.Task,
        ] = {}

        self._candidate_tasks: dict[
            str,
            asyncio.Task,
        ] = {}

        self._decision_locks: dict[
            str,
            asyncio.Lock,
        ] = {}

    async def initialize(
        self,
        department_id: str,
    ) -> None:
        await self.evaluate_department(
            department_id,
        )

        pending = (
            await self.promotion_service
            .get_pending_requests()
        )

        for request in pending:
            self._schedule_timeout(
                request,
            )

    async def evaluate_department(
        self,
        department_id: str,
    ) -> None:
        entries = (
            await self.queue_service
            .get_department_entries(
                department_id,
            )
        )

        for entry in entries:
            await self.evaluate_entry(
                entry,
            )

    async def evaluate_entry(
        self,
        entry: QueueEntry,
    ) -> PromotionRequest | None:
        if entry.status not in {
            QueueStatus.WAITING,
            QueueStatus.PROMOTION_PENDING,
        }:
            self._cancel_candidate_task(
                entry.queue_entry_id,
            )

            return None

        if entry.doctor_id is None:
            self._cancel_candidate_task(
                entry.queue_entry_id,
            )

            return None

        latest = (
            await self.promotion_service
            .get_latest_queue_request(
                entry.queue_entry_id,
            )
        )

        if latest is not None:
            if (
                latest.status
                == PromotionStatus.PENDING
            ):
                self._schedule_timeout(
                    latest,
                )

                return latest

            self._cancel_candidate_task(
                entry.queue_entry_id,
            )

            return None

        if (
            entry.status
            == QueueStatus.WAITING
        ):
            self._schedule_candidate_check(
                entry,
            )

            if not self._wait_threshold_reached(
                entry,
            ):
                return None

        target = (
            await self._select_target_doctor(
                entry,
            )
        )

        if target is None:
            if (
                entry.status
                == QueueStatus.PROMOTION_PENDING
            ):
                await self.queue_service.update_entry(
                    entry.queue_entry_id,
                    {
                        "status":
                            QueueStatus.WAITING,
                    },
                )

            return None

        (
            target_doctor_id,
            current_workload,
            target_workload,
        ) = target

        reason = (
            "An eligible doctor currently has "
            f"{target_workload} active assignments "
            "versus "
            f"{current_workload} for the patient's "
            "current doctor; earlier attention may "
            "be available."
        )

        request = (
            await self.promotion_service
            .create_promotion_request(
                queue_entry_id=(
                    entry.queue_entry_id
                ),
                target_doctor_id=(
                    target_doctor_id
                ),
                reason=reason,
            )
        )

        await self.queue_service.update_entry(
            entry.queue_entry_id,
            {
                "status":
                    QueueStatus.PROMOTION_PENDING,
            },
        )

        self._cancel_candidate_task(
            entry.queue_entry_id,
        )

        self._schedule_timeout(
            request,
        )

        return request

    async def create_manual_request(
        self,
        queue_entry_id: str,
        target_doctor_id: str,
        reason: str,
    ) -> PromotionRequest:
        entry = (
            await self.queue_service
            .get_entry(
                queue_entry_id,
            )
        )

        if entry is None:
            raise ValueError(
                "Queue entry not found",
            )

        if entry.doctor_id is None:
            raise ValueError(
                "Queue entry has no assigned doctor",
            )

        if entry.status not in {
            QueueStatus.WAITING,
            QueueStatus.PROMOTION_PENDING,
        }:
            raise ValueError(
                "Queue entry cannot be promoted in its current state",
            )

        target_doctor = (
            await self.doctor_repository
            .get_doctor(
                target_doctor_id,
            )
        )

        if target_doctor is None:
            raise ValueError(
                "Target doctor not found",
            )

        if (
            entry.department_id
            not in target_doctor.department_ids
        ):
            raise ValueError(
                "Target doctor does not belong to this department",
            )

        if not target_doctor.is_available:
            raise ValueError(
                "Target doctor is unavailable",
            )

        existing = (
            await self.promotion_service
            .get_queue_request(
                queue_entry_id,
            )
        )

        if existing is not None:
            raise ValueError(
                "A pending promotion request already exists",
            )

        request = (
            await self.promotion_service
            .create_promotion_request(
                queue_entry_id=queue_entry_id,
                target_doctor_id=target_doctor_id,
                reason=reason,
            )
        )

        await self.queue_service.update_entry(
            queue_entry_id,
            {
                "status":
                    QueueStatus.PROMOTION_PENDING,
            },
        )

        self._schedule_timeout(
            request,
        )

        return request

    async def approve(
        self,
        promotion_request_id: str,
        decided_by: str | None = None,
        decision_reason: str | None = None,
    ) -> PromotionRequest | None:
        lock = self._get_decision_lock(
            promotion_request_id,
        )

        async with lock:
            return await self._approve_locked(
                promotion_request_id,
                decided_by,
                decision_reason,
            )

    async def _approve_locked(
        self,
        promotion_request_id: str,
        decided_by: str | None,
        decision_reason: str | None,
    ) -> PromotionRequest | None:
        request = (
            await self.promotion_service
            .get_request(
                promotion_request_id,
            )
        )

        if request is None:
            return None

        if (
            request.status
            != PromotionStatus.PENDING
        ):
            return request

        if self._is_expired(
            request,
        ):
            return await self._auto_approve_locked(
                promotion_request_id,
            )

        await self.reassignment_service.reassign(
            request.queue_entry_id,
            request.target_doctor_id,
        )

        result = (
            await self.promotion_service
            .approve(
                promotion_request_id,
                decided_by=decided_by,
                decision_reason=decision_reason,
            )
        )

        await self._restore_waiting_state(
            request.queue_entry_id,
        )

        self._cancel_timeout_task(
            promotion_request_id,
        )

        if result is not None:
            await self._reevaluate_department_for_queue_entry(
                request.queue_entry_id,
            )

        return result

    async def deny(
        self,
        promotion_request_id: str,
        decided_by: str | None = None,
        decision_reason: str | None = None,
    ) -> PromotionRequest | None:
        lock = self._get_decision_lock(
            promotion_request_id,
        )

        async with lock:
            return await self._deny_locked(
                promotion_request_id,
                decided_by,
                decision_reason,
            )

    async def _deny_locked(
        self,
        promotion_request_id: str,
        decided_by: str | None,
        decision_reason: str | None,
    ) -> PromotionRequest | None:
        request = (
            await self.promotion_service
            .get_request(
                promotion_request_id,
            )
        )

        if request is None:
            return None

        if (
            request.status
            != PromotionStatus.PENDING
        ):
            return request

        if self._is_expired(
            request,
        ):
            return await self._auto_approve_locked(
                promotion_request_id,
            )

        result = (
            await self.promotion_service
            .deny(
                promotion_request_id,
                decided_by=decided_by,
                decision_reason=decision_reason,
            )
        )

        await self._restore_waiting_state(
            request.queue_entry_id,
        )

        self._cancel_timeout_task(
            promotion_request_id,
        )

        return result

    async def cancel(
        self,
        promotion_request_id: str,
        reason: str | None = None,
    ) -> PromotionRequest | None:
        lock = self._get_decision_lock(
            promotion_request_id,
        )

        async with lock:
            request = (
                await self.promotion_service
                .get_request(
                    promotion_request_id,
                )
            )

            if request is None:
                return None

            if (
                request.status
                != PromotionStatus.PENDING
            ):
                return request

            if self._is_expired(
                request,
            ):
                return (
                    await self._auto_approve_locked(
                        promotion_request_id,
                    )
                )

            result = (
                await self.promotion_service
                .cancel(
                    promotion_request_id,
                    reason,
                )
            )

            await self._restore_waiting_state(
                request.queue_entry_id,
            )

            self._cancel_timeout_task(
                promotion_request_id,
            )

            return result

    async def auto_approve(
        self,
        promotion_request_id: str,
    ) -> PromotionRequest | None:
        lock = self._get_decision_lock(
            promotion_request_id,
        )

        async with lock:
            return await self._auto_approve_locked(
                promotion_request_id,
            )

    async def _auto_approve_locked(
        self,
        promotion_request_id: str,
    ) -> PromotionRequest | None:
        request = (
            await self.promotion_service
            .get_request(
                promotion_request_id,
            )
        )

        if request is None:
            return None

        if (
            request.status
            != PromotionStatus.PENDING
        ):
            return request

        await self.reassignment_service.reassign(
            request.queue_entry_id,
            request.target_doctor_id,
        )

        result = (
            await self.promotion_service
            .auto_approve(
                promotion_request_id,
            )
        )

        await self._restore_waiting_state(
            request.queue_entry_id,
        )

        self._cancel_timeout_task(
            promotion_request_id,
        )

        if result is not None:
            await self._reevaluate_department_for_queue_entry(
                request.queue_entry_id,
            )

        return result

    async def _select_target_doctor(
        self,
        entry: QueueEntry,
    ) -> tuple[
        str,
        int,
        int,
    ] | None:
        doctors = (
            await self.doctor_repository
            .get_department_doctors(
                entry.department_id,
            )
        )

        current_doctor = None
        current_workload = 0

        target_doctor = None
        target_workload = None

        for doctor in doctors:
            if (
                doctor.doctor_id
                == entry.doctor_id
            ):
                current_doctor = doctor

                assignments = (
                    await self.assignment_repository
                    .get_doctor_assignments(
                        doctor.doctor_id,
                    )
                )

                current_workload = len(
                    assignments,
                )

                continue

            if not doctor.is_available:
                continue

            assignments = (
                await self.assignment_repository
                .get_doctor_assignments(
                    doctor.doctor_id,
                )
            )

            workload = len(
                assignments,
            )

            if (
                target_workload is None
                or workload
                < target_workload
            ):
                target_doctor = doctor
                target_workload = workload

        if current_doctor is None:
            return None

        if target_doctor is None:
            return None

        assert target_workload is not None

        if (
            entry.status
            == QueueStatus.PROMOTION_PENDING
        ):
            return (
                target_doctor.doctor_id,
                current_workload,
                target_workload,
            )

        if (
            current_workload
            - target_workload
            < self.MIN_WORKLOAD_ADVANTAGE
        ):
            return None

        return (
            target_doctor.doctor_id,
            current_workload,
            target_workload,
        )

    def _wait_threshold_reached(
        self,
        entry: QueueEntry,
    ) -> bool:
        if entry.queued_at is None:
            return False

        queued_at = self._as_utc(
            entry.queued_at,
        )

        return (
            datetime.now(timezone.utc)
            - queued_at
        ).total_seconds() >= (
            self.MIN_WAIT_SECONDS
        )

    def _schedule_candidate_check(
        self,
        entry: QueueEntry,
    ) -> None:
        if (
            entry.queued_at is None
            or entry.queue_entry_id
            in self._candidate_tasks
        ):
            return

        queued_at = self._as_utc(
            entry.queued_at,
        )

        threshold = (
            queued_at
            + timedelta(
                seconds=self.MIN_WAIT_SECONDS,
            )
        )

        delay = max(
            0,
            (
                threshold
                - datetime.now(
                    timezone.utc,
                )
            ).total_seconds(),
        )

        task = asyncio.create_task(
            self._candidate_after_delay(
                entry.queue_entry_id,
                delay,
            ),
        )

        self._candidate_tasks[
            entry.queue_entry_id
        ] = task

        task.add_done_callback(
            lambda _: self._candidate_tasks.pop(
                entry.queue_entry_id,
                None,
            ),
        )

    async def _candidate_after_delay(
        self,
        queue_entry_id: str,
        delay: float,
    ) -> None:
        await asyncio.sleep(
            delay,
        )

        entry = (
            await self.queue_service
            .get_entry(
                queue_entry_id,
            )
        )

        if entry is not None:
            await self.evaluate_entry(
                entry,
            )

    def _schedule_timeout(
        self,
        request: PromotionRequest,
    ) -> None:
        existing = self._timeout_tasks.get(
            request.promotion_request_id,
        )

        if (
            existing is not None
            and not existing.done()
        ):
            return

        delay = max(
            0,
            (
                self._as_utc(
                    request.decision_deadline,
                )
                - datetime.now(
                    timezone.utc,
                )
            ).total_seconds(),
        )

        task = asyncio.create_task(
            self._auto_approve_after_delay(
                request.promotion_request_id,
                delay,
            ),
        )

        self._timeout_tasks[
            request.promotion_request_id
        ] = task

        task.add_done_callback(
            lambda _: self._timeout_tasks.pop(
                request.promotion_request_id,
                None,
            ),
        )

    async def _auto_approve_after_delay(
        self,
        promotion_request_id: str,
        delay: float,
    ) -> None:
        try:
            await asyncio.sleep(
                delay,
            )

            await self.auto_approve(
                promotion_request_id,
            )
        except asyncio.CancelledError:
            raise
        except ValueError:
            return

    async def _restore_waiting_state(
        self,
        queue_entry_id: str,
    ) -> None:
        entry = (
            await self.queue_service
            .get_entry(
                queue_entry_id,
            )
        )

        if entry is None:
            return

        if (
            entry.status
            == QueueStatus.PROMOTION_PENDING
        ):
            await self.queue_service.update_entry(
                queue_entry_id,
                {
                    "status":
                        QueueStatus.WAITING,
                },
            )

    async def _reevaluate_department_for_queue_entry(
        self,
        queue_entry_id: str,
    ) -> None:
        entry = (
            await self.queue_service
            .get_entry(
                queue_entry_id,
            )
        )

        if entry is None:
            return

        await self.evaluate_department(
            entry.department_id,
        )

    def _get_decision_lock(
        self,
        promotion_request_id: str,
    ) -> asyncio.Lock:
        lock = self._decision_locks.get(
            promotion_request_id,
        )

        if lock is None:
            lock = asyncio.Lock()

            self._decision_locks[
                promotion_request_id
            ] = lock

        return lock

    def _cancel_timeout_task(
        self,
        promotion_request_id: str,
    ) -> None:
        task = self._timeout_tasks.pop(
            promotion_request_id,
            None,
        )

        if (
            task is not None
            and not task.done()
        ):
            task.cancel()

    def _cancel_candidate_task(
        self,
        queue_entry_id: str,
    ) -> None:
        task = self._candidate_tasks.pop(
            queue_entry_id,
            None,
        )

        if (
            task is not None
            and not task.done()
        ):
            task.cancel()

    @staticmethod
    def _is_expired(
        request: PromotionRequest,
    ) -> bool:
        deadline = PromotionWorkflowService ._as_utc(request.decision_deadline)

        return (
            datetime.now(
                timezone.utc,
            )
            >= deadline
        )

    @staticmethod
    def _as_utc(
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc,
            )

        return value.astimezone(
            timezone.utc,
        )

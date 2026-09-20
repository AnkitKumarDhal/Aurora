from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.database.repositories.promotion import (
    PromotionRepository,
)
from backend.domain.enums import PromotionStatus
from backend.domain.promotion import (
    PromotionRequest,
)
from backend.models.promotion import (
    PromotionRequestDocument,
)


class PromotionService:
    DECISION_WINDOW_SECONDS = 60

    def __init__(
        self,
        repository: PromotionRepository,
    ) -> None:
        self.repository = repository

    async def get_request(
        self,
        promotion_request_id: str,
    ) -> PromotionRequest | None:
        document = (
            await self.repository
            .get_request(
                promotion_request_id,
            )
        )

        if document is None:
            return None

        return self._to_domain(
            document,
        )

    async def get_queue_request(
        self,
        queue_entry_id: str,
    ) -> PromotionRequest | None:
        document = (
            await self.repository
            .get_queue_request(
                queue_entry_id,
            )
        )

        if document is None:
            return None

        return self._to_domain(
            document,
        )

    async def get_latest_queue_request(
        self,
        queue_entry_id: str,
    ) -> PromotionRequest | None:
        document = (
            await self.repository
            .get_latest_queue_request(
                queue_entry_id,
            )
        )

        if document is None:
            return None

        return self._to_domain(
            document,
        )

    async def get_pending_requests(
        self,
    ) -> list[PromotionRequest]:
        documents = (
            await self.repository
            .get_pending_requests()
        )

        return [
            self._to_domain(
                document,
            )
            for document in documents
        ]

    async def create_request(
        self,
        request: PromotionRequest,
    ) -> PromotionRequest:
        document = self._to_document(
            request,
        )

        await self.repository.create_request(
            document,
        )

        return request

    async def create_promotion_request(
        self,
        queue_entry_id: str,
        target_doctor_id: str,
        reason: str,
    ) -> PromotionRequest:
        existing = (
            await self.repository
            .get_queue_request(
                queue_entry_id,
            )
        )

        if existing is not None:
            raise ValueError(
                "A pending promotion request already exists",
            )

        now = datetime.now(
            timezone.utc,
        )

        request = PromotionRequest(
            promotion_request_id=(
                f"promotion_{uuid4().hex}"
            ),
            queue_entry_id=(
                queue_entry_id
            ),
            target_doctor_id=(
                target_doctor_id
            ),
            reason=reason,
            status=PromotionStatus.PENDING,
            decision_deadline=(
                now
                + timedelta(
                    seconds=(
                        self.DECISION_WINDOW_SECONDS
                    ),
                )
            ),
            decided_by=None,
            decision_reason=None,
            decided_at=None,
            created_at=now,
            updated_at=now,
        )

        return await self.create_request(
            request,
        )

    async def approve(
        self,
        promotion_request_id: str,
        decided_by: str | None = None,
        decision_reason: str | None = None,
    ) -> PromotionRequest | None:
        request = (
            await self.repository
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
            return self._to_domain(
                request,
            )

        if self._is_expired(
            request,
        ):
            return await self.auto_approve(
                promotion_request_id,
            )

        return await self._update_decision(
            promotion_request_id,
            PromotionStatus.APPROVED,
            decided_by,
            decision_reason,
        )

    async def deny(
        self,
        promotion_request_id: str,
        decided_by: str | None = None,
        decision_reason: str | None = None,
    ) -> PromotionRequest | None:
        request = (
            await self.repository
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
            return self._to_domain(
                request,
            )

        if self._is_expired(
            request,
        ):
            return await self.auto_approve(
                promotion_request_id,
            )

        return await self._update_decision(
            promotion_request_id,
            PromotionStatus.DENIED,
            decided_by,
            decision_reason,
        )

    async def auto_approve(
        self,
        promotion_request_id: str,
    ) -> PromotionRequest | None:
        request = (
            await self.repository
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
            return self._to_domain(
                request,
            )

        return await self._update_decision(
            promotion_request_id,
            PromotionStatus.AUTO_APPROVED,
            None,
            "Promotion decision window expired.",
        )

    async def cancel(
        self,
        promotion_request_id: str,
        reason: str | None = None,
    ) -> PromotionRequest | None:
        request = (
            await self.repository
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
            return self._to_domain(
                request,
            )

        if self._is_expired(
            request,
        ):
            return await self.auto_approve(
                promotion_request_id,
            )

        return await self._update_decision(
            promotion_request_id,
            PromotionStatus.CANCELLED,
            None,
            reason,
        )

    async def expire_pending_requests(
        self,
    ) -> list[PromotionRequest]:
        requests = (
            await self.repository
            .get_pending_requests()
        )

        expired: list[PromotionRequest] = []

        for request in requests:
            if self._is_expired(
                request,
            ):
                result = (
                    await self.auto_approve(
                        request.promotion_request_id,
                    )
                )

                if result is not None:
                    expired.append(
                        result,
                    )

        return expired

    async def _update_decision(
        self,
        promotion_request_id: str,
        status: PromotionStatus,
        decided_by: str | None,
        decision_reason: str | None,
    ) -> PromotionRequest | None:
        timestamp = datetime.now(
            timezone.utc,
        )

        document = (
            await self.repository
            .update_request(
                promotion_request_id,
                {
                    "status": status,
                    "decided_by": decided_by,
                    "decision_reason":
                        decision_reason,
                    "decided_at":
                        timestamp,
                    "updated_at":
                        timestamp,
                },
            )
        )

        if document is None:
            return None

        return self._to_domain(
            document,
        )

    @staticmethod
    def _is_expired(
        request: PromotionRequestDocument,
    ) -> bool:
        deadline = (
            PromotionService._as_utc(
                request.decision_deadline,
            )
        )

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

    @staticmethod
    def _to_domain(
        document: PromotionRequestDocument,
    ) -> PromotionRequest:
        return PromotionRequest(
            promotion_request_id=(
                document
                .promotion_request_id
            ),
            queue_entry_id=(
                document
                .queue_entry_id
            ),
            target_doctor_id=(
                document
                .target_doctor_id
            ),
            reason=document.reason,
            status=document.status,
            decision_deadline=(
                PromotionService._as_utc(
                    document
                    .decision_deadline,
                )
            ),
            decided_by=(
                document.decided_by
            ),
            decision_reason=(
                document
                .decision_reason
            ),
            decided_at=(
                PromotionService._as_utc(
                    document.decided_at
                )
                if document.decided_at
                is not None
                else None
            ),
            created_at=(
                PromotionService._as_utc(
                    document.created_at,
                )
            ),
            updated_at=(
                PromotionService._as_utc(
                    document.updated_at,
                )
            ),
        )

    @staticmethod
    def _to_document(
        request: PromotionRequest,
    ) -> PromotionRequestDocument:
        return PromotionRequestDocument(
            promotion_request_id=(
                request
                .promotion_request_id
            ),
            queue_entry_id=(
                request
                .queue_entry_id
            ),
            target_doctor_id=(
                request
                .target_doctor_id
            ),
            reason=request.reason,
            status=request.status,
            decision_deadline=(
                PromotionService._as_utc(
                    request
                    .decision_deadline,
                )
            ),
            decided_by=request.decided_by,
            decision_reason=(
                request
                .decision_reason
            ),
            decided_at=(
                PromotionService._as_utc(
                    request.decided_at
                )
                if request.decided_at
                is not None
                else None
            ),
            created_at=(
                PromotionService._as_utc(
                    request.created_at,
                )
                if request.created_at
                is not None
                else datetime.now(
                    timezone.utc,
                )
            ),
            updated_at=(
                PromotionService._as_utc(
                    request.updated_at,
                )
                if request.updated_at
                is not None
                else datetime.now(
                    timezone.utc,
                )
            ),
        )

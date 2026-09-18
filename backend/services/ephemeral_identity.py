from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.integrations.identity import (
    IdentityOtpChallenge,
    IdentityVerificationResult,
    MockIdentityProvider,
)


@dataclass(frozen=True)
class EphemeralVerification:
    token: str
    draft_id: str
    method: str
    identifier: str
    result: IdentityVerificationResult
    expires_at: datetime


class EphemeralIdentityService:
    VERIFICATION_TTL_SECONDS = 900

    def __init__(self, identity_provider: MockIdentityProvider) -> None:
        self.identity_provider = identity_provider
        self._verifications: dict[str, EphemeralVerification] = {}

    async def request_otp(
        self,
        draft_id: str,
        method: str,
        identifier: str,
    ) -> IdentityOtpChallenge:
        return await self.identity_provider.request_otp(
            draft_id,
            method,
            identifier,
        )

    async def verify_otp(
        self,
        draft_id: str,
        challenge_id: str,
        otp: str,
    ) -> EphemeralVerification:
        verification = await self.identity_provider.verify_otp(
            draft_id,
            challenge_id,
            otp,
        )

        if verification.result.status.value != "VERIFIED":
            raise ValueError("Patient identity could not be verified")

        token = f"ver_{uuid4().hex}"

        record = EphemeralVerification(
            token=token,
            draft_id=draft_id,
            method=verification.method,
            identifier=self._normalize_identifier(
                verification.identifier,
            ),
            result=verification.result,
            expires_at=datetime.now(timezone.utc)
            + timedelta(seconds=self.VERIFICATION_TTL_SECONDS),
        )

        self._verifications[token] = record

        return record

    async def get_verified_identity(
        self,
        draft_id: str,
        token: str,
        method: str,
        identifier: str,
    ) -> EphemeralVerification:
        record = self._verifications.get(token)

        if record is None:
            raise ValueError("Invalid or expired verification")

        if record.draft_id != draft_id:
            raise ValueError("Verification does not belong to this draft")

        normalized_method = method.upper()
        normalized_identifier = self._normalize_identifier(
            identifier,
        )

        if (
            record.method != normalized_method
            or record.identifier != normalized_identifier
        ):
            raise ValueError(
                "Verification does not match the submitted identity",
            )

        if datetime.now(timezone.utc) >= record.expires_at:
            self._verifications.pop(token, None)
            raise ValueError("Verification has expired")

        return record

    @staticmethod
    def _normalize_identifier(identifier: str) -> str:
        return "".join(
            character
            for character in identifier
            if character.isdigit()
        )

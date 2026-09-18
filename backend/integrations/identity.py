from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
from typing import Protocol
from uuid import uuid4

from backend.domain.enums import VerificationStatus


@dataclass(frozen=True)
class IdentityVerificationResult:
    status: VerificationStatus
    patient_id: str | None = None
    display_name: str | None = None
    date_of_birth: date | None = None
    age: int | None = None
    abha_reference: str | None = None
    aadhaar_reference: str | None = None
    hospital_reference: str | None = None


@dataclass(frozen=True)
class IdentityOtpChallenge:
    challenge_id: str
    masked_destination: str
    expires_in_seconds: int
    demo_otp: str | None = None


@dataclass(frozen=True)
class IdentityOtpVerification:
    method: str
    identifier: str
    result: IdentityVerificationResult


class IdentityProvider(Protocol):
    async def request_otp(
        self,
        session_id: str,
        method: str,
        identifier: str,
    ) -> IdentityOtpChallenge:
        ...

    async def verify_otp(
        self,
        session_id: str,
        challenge_id: str,
        otp: str,
    ) -> IdentityOtpVerification:
        ...

    async def lookup(
        self,
        method: str,
        identifier: str,
    ) -> IdentityVerificationResult:
        ...


class MockIdentityProvider:
    DEMO_OTP = "123456"
    OTP_TTL_SECONDS = 300

    IDENTITIES = {
        (
            "ABHA",
            "11112222333344",
        ): IdentityVerificationResult(
            status=VerificationStatus.VERIFIED,
            patient_id="patient-demo-001",
            display_name="Demo Patient",
            date_of_birth=date(1998, 5, 14),
            age=28,
            abha_reference="11112222333344",
            aadhaar_reference="123456789012",
            hospital_reference="HOSP-0001",
        ),
        (
            "AADHAAR",
            "123456789012",
        ): IdentityVerificationResult(
            status=VerificationStatus.VERIFIED,
            patient_id="patient-demo-001",
            display_name="Demo Patient",
            date_of_birth=date(1998, 5, 14),
            age=28,
            abha_reference="11112222333344",
            aadhaar_reference="123456789012",
            hospital_reference="HOSP-0001",
        ),
        (
            "ABHA",
            "99998888777766",
        ): IdentityVerificationResult(
            status=VerificationStatus.VERIFIED,
            patient_id="patient-demo-002",
            display_name="Demo Patient Two",
            date_of_birth=date(1985, 9, 21),
            age=40,
            abha_reference="99998888777766",
            aadhaar_reference="987654321098",
            hospital_reference="HOSP-0002",
        ),
        (
            "AADHAAR",
            "987654321098",
        ): IdentityVerificationResult(
            status=VerificationStatus.VERIFIED,
            patient_id="patient-demo-002",
            display_name="Demo Patient Two",
            date_of_birth=date(1985, 9, 21),
            age=40,
            abha_reference="99998888777766",
            aadhaar_reference="987654321098",
            hospital_reference="HOSP-0002",
        ),
    }

    _CHALLENGES: dict[
        str,
        tuple[str, str, str, datetime],
    ] = {}

    async def request_otp(
        self,
        session_id: str,
        method: str,
        identifier: str,
    ) -> IdentityOtpChallenge:
        normalized_method = method.upper()
        normalized_identifier = self._normalize_identifier(identifier)

        self._validate_identifier(
            normalized_method,
            normalized_identifier,
        )

        challenge_id = f"otp_{uuid4().hex}"
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=self.OTP_TTL_SECONDS,
        )

        self._CHALLENGES[challenge_id] = (
            session_id,
            normalized_method,
            normalized_identifier,
            expires_at,
        )

        return IdentityOtpChallenge(
            challenge_id=challenge_id,
            masked_destination="registered mobile number",
            expires_in_seconds=self.OTP_TTL_SECONDS,
            demo_otp=self.DEMO_OTP,
        )

    async def verify_otp(
        self,
        session_id: str,
        challenge_id: str,
        otp: str,
    ) -> IdentityOtpVerification:
        challenge = self._CHALLENGES.get(challenge_id)

        if challenge is None:
            raise ValueError("Invalid or expired OTP challenge")

        (
            challenge_session_id,
            method,
            identifier,
            expires_at,
        ) = challenge

        if challenge_session_id != session_id:
            raise ValueError("OTP challenge does not belong to this session")

        if datetime.now(timezone.utc) >= expires_at:
            self._CHALLENGES.pop(challenge_id, None)
            raise ValueError("OTP challenge has expired")

        if otp.strip() != self.DEMO_OTP:
            raise ValueError("Invalid OTP")

        self._CHALLENGES.pop(challenge_id, None)

        result = await self.lookup(
            method,
            identifier,
        )

        return IdentityOtpVerification(
            method=method,
            identifier=identifier,
            result=result,
        )

    async def lookup(
        self,
        method: str,
        identifier: str,
    ) -> IdentityVerificationResult:
        normalized_method = method.upper()
        normalized_identifier = self._normalize_identifier(identifier)

        self._validate_identifier(
            normalized_method,
            normalized_identifier,
        )

        existing_identity = self.IDENTITIES.get(
            (
                normalized_method,
                normalized_identifier,
            ),
        )

        if existing_identity is not None:
            return existing_identity

        digest = hashlib.sha256(
            f"{normalized_method}:{normalized_identifier}".encode(),
        ).hexdigest()

        patient_id = f"patient-demo-{digest[:12]}"
        display_name = f"Demo Patient {normalized_identifier[-4:]}"
        hospital_reference = f"HOSP-DEMO-{digest[:8].upper()}"

        return IdentityVerificationResult(
            status=VerificationStatus.VERIFIED,
            patient_id=patient_id,
            display_name=display_name,
            abha_reference=(
                normalized_identifier
                if normalized_method == "ABHA"
                else None
            ),
            aadhaar_reference=(
                normalized_identifier
                if normalized_method == "AADHAAR"
                else None
            ),
            hospital_reference=hospital_reference,
        )

    @staticmethod
    def _validate_identifier(
        method: str,
        identifier: str,
    ) -> None:
        if method not in {"ABHA", "AADHAAR"}:
            raise ValueError("Unsupported identity method")

        expected_length = 14 if method == "ABHA" else 12

        if (
            len(identifier) != expected_length
            or not identifier.isdigit()
        ):
            raise ValueError(
                f"{method} identifier must contain "
                f"{expected_length} digits",
            )

    @staticmethod
    def _normalize_identifier(identifier: str) -> str:
        return "".join(
            character
            for character in identifier
            if character.isdigit()
        )

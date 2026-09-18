from dataclasses import dataclass
from datetime import date
from typing import Protocol

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


class IdentityProvider(Protocol):
    async def verify(
        self,
        method: str,
        identifier: str,
    ) -> IdentityVerificationResult:
        ...


class MockIdentityProvider:
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

    async def verify(
        self,
        method: str,
        identifier: str,
    ) -> IdentityVerificationResult:
        normalized_method = method.upper()
        normalized_identifier = "".join(
            character
            for character in identifier
            if character.isdigit()
        )

        result = self.IDENTITIES.get(
            (
                normalized_method,
                normalized_identifier,
            ),
        )

        if result is None:
            return IdentityVerificationResult(
                status=VerificationStatus.FAILED,
            )

        return result

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
    hospital_reference: str | None = None


class IdentityProvider(Protocol):
    async def verify(self, method: str, identifier: str,) -> IdentityVerificationResult:
        ...


class MockIdentityProvider:
    PATIENTS = {
        "1111-2222-3333": IdentityVerificationResult(
            status=VerificationStatus.VERIFIED,
            patient_id="patient-demo-001",
            display_name="Demo Patient",
            date_of_birth=date(1998, 5, 14),
            age=28,
            abha_reference="11-22-33-44-55-66",
            hospital_reference="HOSP-0001",
        ),
        "9999-8888-7777": IdentityVerificationResult(
            status=VerificationStatus.VERIFIED,
            patient_id="patient-demo-002",
            display_name="Demo Patient Two",
            date_of_birth=date(1985, 9, 21),
            age=40,
            abha_reference="99-88-77-66-55-44",
            hospital_reference="HOSP-0002",
        ),
    }

    async def verify(
        self,
        method: str,
        identifier: str,
    ) -> IdentityVerificationResult:
        if method.upper() != "ABHA":
            return IdentityVerificationResult(
                status=VerificationStatus.FAILED,
            )

        result = self.PATIENTS.get(identifier.strip())

        if result is None:
            return IdentityVerificationResult(
                status=VerificationStatus.FAILED,
            )

        return result

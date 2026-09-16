from dataclasses import dataclass
from typing import Protocol


@dataclass
class AbhaProfile:
    abha_id: str
    display_name: str
    date_of_birth: str | None = None
    gender: str | None = None


class AbdmClient(Protocol):
    async def get_profile(self, abha_id: str) -> AbhaProfile | None:
        ...


class MockAbdmClient:
    def __init__(self) -> None:
        self.profiles = {
            "11-22-33-44-55-66": AbhaProfile(
                abha_id="11-22-33-44-55-66",
                display_name="Demo Patient",
                date_of_birth="1998-05-14",
            ),
            "99-88-77-66-55-44": AbhaProfile(
                abha_id="99-88-77-66-55-44",
                display_name="Demo Patient Two",
                date_of_birth="1985-09-21",
            ),
        }

    async def get_profile(self, abha_id: str) -> AbhaProfile | None:
        return self.profiles.get(abha_id)

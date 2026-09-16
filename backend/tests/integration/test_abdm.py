import pytest
from backend.integrations.abdm import MockAbdmClient


@pytest.mark.asyncio
async def test_get_known_abha_profile():
    client = MockAbdmClient()

    profile = await client.get_profile("11-22-33-44-55-66")

    assert profile is not None
    assert profile.abha_id == "11-22-33-44-55-66"
    assert profile.display_name == "Demo Patient"


@pytest.mark.asyncio
async def test_get_unknown_abha_profile():
    client = MockAbdmClient()

    profile = await client.get_profile("00-00-00-00-00-00")

    assert profile is None

from fastapi import APIRouter

from backend.api.schemas.consent import ConsentInformationResponse
from backend.services.consent import ConsentService

router = APIRouter(
    prefix="/consent-information",
    tags=["consent"],
)


@router.get("", response_model=dict)
async def get_consent_information(
    language: str = "en",
) -> dict:
    information = ConsentService.get_information(language)

    response = ConsentInformationResponse(
        version=information["version"],
        status="AVAILABLE",
        text=information["text"],
        audio_available=information["audio_available"],
        supported_languages=information["supported_languages"],
    )

    return {
        "data": response.model_dump(mode="json"),
    }

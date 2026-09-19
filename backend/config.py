from functools import lru_cache

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    environment: str = "development"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_database: str = "aurora"

    cors_origins: str = (
        "http://localhost:5173,"
        "http://localhost:5174,"
        "http://localhost:5175"
    )

    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 60

    identity_demo_mode: bool = False

    interview_ai_enabled: bool = Field(
        default=True,
        validation_alias="AURORA_INTERVIEW_AI_ENABLED",
    )

    interview_ai_provider: str = Field(
        default="lemonade",
        validation_alias="AURORA_INTERVIEW_AI_PROVIDER",
    )

    interview_max_followups: int = Field(
        default=7,
        ge=1,
        le=20,
        validation_alias="AURORA_INTERVIEW_MAX_FOLLOWUPS",
    )

    lemonade_url: str = Field(
        default="http://127.0.0.1:13305/api/v1/chat/completions",
        validation_alias="AURORA_LEMONADE_URL",
    )

    lemonade_model: str = Field(
        default="qwen3.5-9b-FLM",
        validation_alias="AURORA_LEMONADE_MODEL",
    )

    lemonade_timeout: float = Field(
        default=20.0,
        gt=1.0,
        le=120.0,
        validation_alias="AURORA_LEMONADE_TIMEOUT",
    )

    lemonade_json_mode: bool = Field(
        default=True,
        validation_alias="AURORA_LEMONADE_JSON_MODE",
    )

    lemonade_fallback_openrouter: bool = Field(
        default=False,
        validation_alias="AURORA_LEMONADE_FALLBACK_OPENROUTER",
    )

    model_config = SettingsConfigDict(
        env_file="backend/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def interview_max_turns(self) -> int:
        # One initial patient answer + configured follow-ups.
        return 1 + self.interview_max_followups


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

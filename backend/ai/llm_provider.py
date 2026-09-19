from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from dotenv import load_dotenv

try:
    import requests
except ImportError:
    requests = None


_BACKEND_ENV = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_BACKEND_ENV, override=False)

logger = logging.getLogger(__name__)


class JsonLLMProvider(Protocol):
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any] | None:
        ...


def _parse_json(
    content: str,
) -> dict[str, Any] | None:
    text = str(content or "").strip()

    if not text:
        return None

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None

    return parsed if isinstance(parsed, dict) else None


@dataclass
class OpenRouterProvider:
    api_key: str
    primary_model: str
    fallback_models: tuple[str, ...]
    timeout_seconds: float

    url = "https://openrouter.ai/api/v1/chat/completions"

    @property
    def fallback_model(self) -> str | None:
        """Backward-compatible access to the first fallback model."""
        return self.fallback_models[0] if self.fallback_models else None

    @property
    def models(self) -> list[str]:
        """Return the complete model chain in priority order."""
        result: list[str] = []

        for model in (self.primary_model, *self.fallback_models):
            model = model.strip()

            if model and model not in result:
                result.append(model)

        return result

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any] | None:
        if requests is None:
            logger.error(
                "OpenRouter provider requires the requests package"
            )
            return None

        models = self.models

        if not models:
            logger.error("OpenRouter provider has no configured models")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": "Aurora Clinical Interviewer",
        }

        payload = {
            # OpenRouter uses this list for model-level fallback.
            "models": models,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": 0,
            "max_tokens": 500,
            "response_format": {
                "type": "json_object",
            },
            "provider": {
                # Allow OpenRouter to fail over between providers
                # serving the selected model.
                "allow_fallbacks": True,

                # Only use providers that support every requested
                # parameter, including response_format.
                "require_parameters": True,
            },
        }

        try:
            response = requests.post(
                self.url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )

            if not response.ok:
                self._log_error_response(
                    models=models,
                    response=response,
                )
                return None

            try:
                body = response.json()
            except ValueError:
                logger.warning(
                    "OpenRouter returned a non-JSON HTTP response: "
                    "models=%s status=%s",
                    models,
                    response.status_code,
                )
                return None

            choices = body.get("choices") or []

            if not choices:
                logger.warning(
                    "OpenRouter returned no choices: models=%s response=%s",
                    models,
                    body,
                )
                return None

            message = choices[0].get("message") or {}
            content = message.get("content", "")

            parsed = _parse_json(content)

            if parsed is None:
                logger.warning(
                    "OpenRouter returned invalid JSON: models=%s content=%r",
                    models,
                    content,
                )

            return parsed

        except requests.RequestException:
            logger.exception(
                "OpenRouter request failed: models=%s",
                models,
            )
            return None

        except Exception:
            logger.exception(
                "Unexpected OpenRouter provider error: models=%s",
                models,
            )
            return None

    @staticmethod
    def _log_error_response(
        models: list[str],
        response: Any,
    ) -> None:
        try:
            body = response.json()
        except Exception:
            body = response.text

        logger.warning(
            "OpenRouter request failed: status=%s models=%s response=%s",
            response.status_code,
            models,
            body,
        )


@dataclass
class OllamaProvider:
    model: str
    url: str
    timeout_seconds: float

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any] | None:
        if requests is None:
            logger.error(
                "Ollama provider requires the requests package"
            )
            return None

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
            },
        }

        try:
            response = requests.post(
                self.url,
                json=payload,
                timeout=self.timeout_seconds,
            )

            if not response.ok:
                logger.warning(
                    "Ollama request failed: status=%s response=%s",
                    response.status_code,
                    response.text,
                )
                return None

            try:
                body = response.json()
            except ValueError:
                logger.warning(
                    "Ollama returned a non-JSON HTTP response"
                )
                return None

            content = (
                body
                .get("message", {})
                .get("content", "")
            )

            parsed = _parse_json(content)

            if parsed is None:
                logger.warning(
                    "Ollama returned invalid JSON: content=%r",
                    content,
                )

            return parsed

        except requests.RequestException:
            logger.exception(
                "Ollama request failed"
            )
            return None

        except Exception:
            logger.exception(
                "Unexpected Ollama provider error"
            )
            return None


def build_interviewer_provider() -> JsonLLMProvider | None:
    enabled = (
        os.getenv(
            "AURORA_INTERVIEW_AI_ENABLED",
            "0",
        )
        .strip()
        .lower()
        not in {
            "0",
            "false",
            "no",
            "off",
        }
    )

    if not enabled:
        return None

    provider = os.getenv(
        "AURORA_INTERVIEW_AI_PROVIDER",
        "openrouter",
    ).strip().lower()

    try:
        timeout_seconds = float(
            os.getenv(
                "AURORA_INTERVIEW_AI_TIMEOUT",
                "20",
            )
        )
    except ValueError:
        timeout_seconds = 20.0

    if provider == "openrouter":
        api_key = os.getenv(
            "OPENROUTER_API_KEY",
            "",
        ).strip()

        if not api_key:
            logger.warning(
                "OpenRouter selected but OPENROUTER_API_KEY is missing"
            )
            return None

        primary_model = (
            os.getenv(
                "AURORA_OPENROUTER_MODEL",
                os.getenv(
                    "OPENROUTER_PRIMARY_MODEL",
                    "deepseek/deepseek-v4-flash-0731:free",
                ),
            )
            .strip()
        )

        configured_fallbacks = os.getenv(
            "AURORA_OPENROUTER_FALLBACK_MODELS",
            "",
        ).strip()

        if configured_fallbacks:
            fallback_models = tuple(
                model.strip()
                for model in configured_fallbacks.split(",")
                if model.strip()
            )
        else:
            # Keep legacy configuration working while providing
            # a current structured-output-capable fallback.
            legacy_fallback = os.getenv(
                "AURORA_OPENROUTER_FALLBACK_MODEL",
                os.getenv(
                    "OPENROUTER_FALLBACK_MODEL",
                    "mistralai/mistral-small-3.2-24b-instruct:free",
                ),
            ).strip()

            fallback_models = (
                (legacy_fallback,)
                if legacy_fallback
                else (
                    "mistralai/mistral-small-3.2-24b-instruct:free",
                )
            )

        return OpenRouterProvider(
            api_key=api_key,
            primary_model=primary_model,
            fallback_models=fallback_models,
            timeout_seconds=timeout_seconds,
        )

    if provider == "ollama":
        return OllamaProvider(
            model=os.getenv(
                "AURORA_OLLAMA_MODEL",
                "qwen2.5:3b",
            ).strip(),
            url=os.getenv(
                "AURORA_OLLAMA_URL",
                "http://127.0.0.1:11434/api/chat",
            ).strip(),
            timeout_seconds=timeout_seconds,
        )

    logger.warning(
        "Unknown interviewer AI provider: %s",
        provider,
    )

    return None

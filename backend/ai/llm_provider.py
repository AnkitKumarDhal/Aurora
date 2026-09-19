from __future__ import annotations

import json
import logging
import os
import re
import time
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
    content: str | None,
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
class LemonadeProvider:
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
                "Lemonade provider requires the requests package",
            )
            return None

        headers = {
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
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

            # The interviewer must be deterministic enough for
            # our validator/controller.
            "temperature": 0,

            # The planner only needs to return a tiny JSON decision.
            "max_tokens": 300,

            # Qwen reasoning is unnecessary for this task.
            # Disable the hidden <think> generation so the small
            # output budget is spent on the actual JSON response.
            "chat_template_kwargs": {
                "enable_thinking": False,
            },

            "response_format": {
                "type": "json_object",
            },
        }

        started = time.perf_counter()

        try:
            response = requests.post(
                self.url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException:
            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000

            logger.warning(
                "Lemonade request failed: "
                "model=%s elapsed_ms=%.1f",
                self.model,
                elapsed_ms,
            )
            return None
        except Exception:
            logger.exception(
                "Unexpected Lemonade provider error: model=%s",
                self.model,
            )
            return None

        elapsed_ms = (
            time.perf_counter() - started
        ) * 1000

        if not response.ok:
            self._log_error_response(
                response=response,
                model=self.model,
                elapsed_ms=elapsed_ms,
            )
            return None

        try:
            body = response.json()
        except ValueError:
            logger.warning(
                "Lemonade returned a non-JSON HTTP response: "
                "model=%s status=%s elapsed_ms=%.1f",
                self.model,
                response.status_code,
                elapsed_ms,
            )
            return None

        choices = body.get("choices") or []

        if not choices:
            logger.warning(
                "Lemonade returned no choices: "
                "model=%s elapsed_ms=%.1f response=%s",
                self.model,
                elapsed_ms,
                body,
            )
            return None

        choice = choices[0] or {}
        message = choice.get("message") or {}

        content = message.get("content")
        finish_reason = choice.get("finish_reason")

        if not content:
            logger.warning(
                "Lemonade returned empty message content: "
                "model=%s finish_reason=%s elapsed_ms=%.1f message=%s",
                self.model,
                finish_reason,
                elapsed_ms,
                message,
            )
            return None

        parsed = _parse_json(content)

        if parsed is None:
            logger.warning(
                "Lemonade returned invalid JSON: "
                "model=%s finish_reason=%s elapsed_ms=%.1f "
                "content=%r",
                self.model,
                finish_reason,
                elapsed_ms,
                content,
            )
            return None

        logger.info(
            "Lemonade interviewer success: "
            "model=%s elapsed_ms=%.1f",
            self.model,
            elapsed_ms,
        )

        return parsed

    @staticmethod
    def _log_error_response(
        response: Any,
        model: str,
        elapsed_ms: float,
    ) -> None:
        try:
            body = response.json()
        except Exception:
            body = response.text

        logger.warning(
            "Lemonade request failed: "
            "status=%s model=%s elapsed_ms=%.1f response=%s",
            response.status_code,
            model,
            elapsed_ms,
            body,
        )


@dataclass
class OpenRouterProvider:
    api_key: str
    primary_model: str
    fallback_models: tuple[str, ...]
    timeout_seconds: float

    url = "https://openrouter.ai/api/v1/chat/completions"

    @property
    def fallback_model(self) -> str | None:
        return (
            self.fallback_models[0]
            if self.fallback_models
            else None
        )

    @property
    def models(self) -> list[str]:
        result: list[str] = []

        for model in (
            self.primary_model,
            *self.fallback_models,
        ):
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
                "OpenRouter provider requires the requests package",
            )
            return None

        models = self.models

        if not models:
            logger.error(
                "OpenRouter provider has no configured models",
            )
            return None

        for model in models:
            result = self._generate_with_model(
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            if result is not None:
                logger.info(
                    "OpenRouter model succeeded: model=%s",
                    model,
                )
                return result

            logger.warning(
                "OpenRouter model produced no valid JSON; "
                "trying next model: model=%s",
                model,
            )

        logger.warning(
            "All OpenRouter interviewer models failed: models=%s",
            models,
        )

        return None

    def _generate_with_model(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any] | None:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": "Aurora Clinical Interviewer",
        }

        payload: dict[str, Any] = {
            "model": model,
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
            "max_tokens": 300,
            "response_format": {
                "type": "json_object",
            },
            "provider": {
                "allow_fallbacks": True,
                "require_parameters": True,
            },
        }

        if model.startswith("deepseek/"):
            payload["reasoning"] = {
                "effort": "low",
            }

        try:
            response = requests.post(
                self.url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException:
            logger.warning(
                "OpenRouter request failed: model=%s",
                model,
            )
            return None
        except Exception:
            logger.exception(
                "Unexpected OpenRouter provider error: model=%s",
                model,
            )
            return None

        if not response.ok:
            self._log_error_response(
                model=model,
                response=response,
            )
            return None

        try:
            body = response.json()
        except ValueError:
            logger.warning(
                "OpenRouter returned a non-JSON HTTP response: "
                "model=%s status=%s",
                model,
                response.status_code,
            )
            return None

        choices = body.get("choices") or []

        if not choices:
            logger.warning(
                "OpenRouter returned no choices: model=%s response=%s",
                model,
                body,
            )
            return None

        choice = choices[0] or {}
        message = choice.get("message") or {}

        content = message.get("content")
        finish_reason = choice.get("finish_reason")

        if not content:
            logger.warning(
                "OpenRouter returned empty message content: "
                "model=%s finish_reason=%s message=%s",
                model,
                finish_reason,
                message,
            )
            return None

        parsed = _parse_json(content)

        if parsed is None:
            logger.warning(
                "OpenRouter returned invalid JSON: "
                "model=%s finish_reason=%s content=%r",
                model,
                finish_reason,
                content,
            )
            return None

        return parsed

    @staticmethod
    def _log_error_response(
        model: str,
        response: Any,
    ) -> None:
        try:
            body = response.json()
        except Exception:
            body = response.text

        logger.warning(
            "OpenRouter request failed: "
            "status=%s model=%s response=%s",
            response.status_code,
            model,
            body,
        )


@dataclass
class FallbackJsonProvider:
    primary: JsonLLMProvider
    fallback: JsonLLMProvider

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any] | None:
        result = self.primary.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        if result is not None:
            return result

        logger.warning(
            "Primary interviewer provider failed; "
            "using remote fallback",
        )

        return self.fallback.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
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
                "Ollama provider requires the requests package",
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
                    "Ollama returned a non-JSON HTTP response",
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
                "Ollama request failed",
            )
            return None

        except Exception:
            logger.exception(
                "Unexpected Ollama provider error",
            )
            return None


def _build_openrouter_provider(
    timeout_seconds: float,
) -> OpenRouterProvider | None:
    api_key = os.getenv(
        "OPENROUTER_API_KEY",
        "",
    ).strip()

    if not api_key:
        logger.warning(
            "OpenRouter selected but OPENROUTER_API_KEY is missing",
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
        legacy_fallback = os.getenv(
            "AURORA_OPENROUTER_FALLBACK_MODEL",
            os.getenv(
                "OPENROUTER_FALLBACK_MODEL",
                "",
            ),
        ).strip()

        fallback_models = (
            (legacy_fallback,)
            if legacy_fallback
            else ()
        )

    return OpenRouterProvider(
        api_key=api_key,
        primary_model=primary_model,
        fallback_models=fallback_models,
        timeout_seconds=timeout_seconds,
    )


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
        "lemonade",
    ).strip().lower()

    try:
        timeout_seconds = float(
            os.getenv(
                "AURORA_INTERVIEW_AI_TIMEOUT",
                "12",
            )
        )
    except ValueError:
        timeout_seconds = 12.0

    if provider == "lemonade":
        try:
            lemonade_timeout = float(
                os.getenv(
                    "AURORA_LEMONADE_TIMEOUT",
                    str(timeout_seconds),
                )
            )
        except ValueError:
            lemonade_timeout = timeout_seconds

        lemonade = LemonadeProvider(
            model=os.getenv(
                "AURORA_LEMONADE_MODEL",
                "qwen3.5-9b-FLM",
            ).strip(),
            url=os.getenv(
                "AURORA_LEMONADE_URL",
                "http://127.0.0.1:13305/api/v1/chat/completions",
            ).strip(),
            timeout_seconds=lemonade_timeout,
        )

        fallback_enabled = (
            os.getenv(
                "AURORA_LEMONADE_FALLBACK_OPENROUTER",
                "1",
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

        if not fallback_enabled:
            return lemonade

        openrouter = _build_openrouter_provider(
            timeout_seconds=timeout_seconds,
        )

        if openrouter is None:
            return lemonade

        return FallbackJsonProvider(
            primary=lemonade,
            fallback=openrouter,
        )

    if provider == "openrouter":
        return _build_openrouter_provider(
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

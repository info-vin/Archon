"""Shared Gemini Decisions API client (POST /v1beta/decisions) with dual-key rotation and TokenUsageService logging."""

import uuid
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx

from ...config.logfire_config import get_logger
from ...config.model_ssot import get_model_path

logger = get_logger(__name__)


class DecisionsUnavailableError(RuntimeError):
    """Raised when Gemini Decisions API cannot serve a request so callers can fall back cleanly."""


@dataclass(frozen=True)
class DecisionChoiceResult:
    """Structured result from a single-select choice question on Gemini Decisions API."""

    choice: str
    confidence: float
    probabilities: dict[str, float]
    input_tokens: int


class DecisionsClient:
    """DRY async client for Gemini Decisions API (`gemini-decision-1`)."""

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _resolve_endpoint() -> str:
        from ...schemas.settings import NetworkConfig
        from ..settings_service import SettingsService

        base_url = NetworkConfig().google_base_url
        try:
            net_cfg = NetworkConfig.model_validate(SettingsService().get_all_settings())
            if net_cfg.google_base_url:
                base_url = net_cfg.google_base_url
        except Exception:
            pass
        parsed = urlsplit(base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else base_url.rstrip("/")
        return f"{origin}/v1beta/decisions"

    @staticmethod
    async def _get_api_keys() -> list[str]:
        from ..credential_service import credential_service

        keys: list[str] = []
        for key_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            try:
                val = await credential_service.get_credential(key_name)
            except Exception as exc:
                logger.debug(f"DecisionsClient: Failed to load {key_name}: {exc}")
                continue
            if val and str(val).strip() and str(val).strip() not in keys:
                keys.append(str(val).strip())
        return keys

    async def classify_choice(
        self,
        *,
        input_text: str,
        question_key: str,
        instructions: str,
        criteria: dict[str, str],
        context_type: str,
    ) -> DecisionChoiceResult:
        """Call Gemini Decisions API with a `choice` question; raises DecisionsUnavailableError on any failure."""
        if len(criteria) < 2:
            raise DecisionsUnavailableError("Decisions API requires at least 2 criteria options.")

        api_keys = await self._get_api_keys()
        if not api_keys:
            raise DecisionsUnavailableError("No GEMINI_API_KEY or GOOGLE_API_KEY available for Decisions API.")

        model_path = get_model_path("DECISION_MODEL")
        model_id = model_path.replace("models/", "")
        endpoint = self._resolve_endpoint()
        payload: dict[str, Any] = {
            "model": model_id,
            "input": input_text,
            "questions": {
                question_key: {
                    "type": "choice",
                    "instructions": instructions,
                    "criteria": criteria,
                }
            },
        }

        last_err: str = "unknown error"
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for api_key in api_keys:
                try:
                    resp = await client.post(
                        endpoint,
                        json=payload,
                        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                    )
                except Exception as exc:
                    last_err = f"{type(exc).__name__}: {exc}"
                    continue

                if resp.status_code != 200:
                    last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    continue

                try:
                    body = resp.json()
                    ans = body["answers"][question_key]
                    choice = str(ans["choice"])
                    confidence = float(ans.get("confidence", 0.0))
                    probs_raw = ans.get("probabilities") or {}
                    probabilities = {str(k): float(v) for k, v in probs_raw.items()}
                    input_tokens = int((body.get("usage") or {}).get("total_input_tokens", 0))
                except Exception as exc:
                    last_err = f"Malformed Decisions API response: {exc}"
                    continue

                if choice not in criteria:
                    last_err = f"Choice '{choice}' not in criteria keys {list(criteria.keys())}"
                    continue

                await self._log_usage(model_path=model_path, input_tokens=input_tokens, context_type=context_type)
                return DecisionChoiceResult(
                    choice=choice,
                    confidence=max(0.0, min(1.0, confidence)),
                    probabilities=probabilities,
                    input_tokens=input_tokens,
                )

        raise DecisionsUnavailableError(f"Decisions API unavailable ({model_id}): {last_err}")

    @staticmethod
    async def _log_usage(*, model_path: str, input_tokens: int, context_type: str) -> None:
        try:
            from ..token_usage_service import TokenUsageService

            await TokenUsageService.log_usage(
                request_id=str(uuid.uuid4()),
                model=model_path,
                provider="gemini",
                input_tokens=input_tokens,
                output_tokens=0,
                context_type=context_type,
            )
        except Exception as exc:
            logger.warning(f"Failed to log Decisions API token usage: {exc}")


decisions_client = DecisionsClient()

import asyncio
import uuid
from typing import Any

from google import genai
from google.genai import types

from ...config.model_ssot import SYSTEM_MODELS
from ...utils.retry_utils import retry_with_backoff
from ..log_service import LogService
from ..prompt_service import prompt_service
from ..token_usage_service import TokenUsageService
from .content_handler import get_logger

logger = get_logger(__name__)


class SalesPitchGenerator:
    """Handles sales pitch AI generation workflows."""

    def __init__(self, supabase_client: Any) -> None:
        self.supabase_client = supabase_client

    async def generate_pitch(self, company: str, job_title: str) -> dict:
        try:
            from ..credential_service import credential_service
            api_key = await credential_service.get_credential("GEMINI_API_KEY")
            if not api_key:
                return {"error_code": 401, "message": "GEMINI_API_KEY missing."}

            rag_strategy_creds = await credential_service.get_credentials_by_category("rag_strategy")
            marketing_model = rag_strategy_creds.get("MARKETING_MODEL") or SYSTEM_MODELS["DEFAULT_TEXT"]

            client = genai.Client(api_key=api_key)
            sys_prompt = prompt_service.get_prompt("SALES_PITCH")

            @retry_with_backoff(max_retries=2)
            async def _call_gemini() -> Any:
                return await client.aio.models.generate_content(
                    model=marketing_model,
                    contents=f"Company: {company}\nRole: {job_title}",
                    config=types.GenerateContentConfig(system_instruction=sys_prompt),
                )

            response = await _call_gemini()

            # Token Logging
            try:
                from ..agent_registry import get_agent_uuid

                agent_uuid = get_agent_uuid("market-bot")
                asyncio.create_task(
                    TokenUsageService.log_usage(
                        request_id=f"pitch-{uuid.uuid4().hex[:8]}",
                        user_id=agent_uuid,
                        model=SYSTEM_MODELS["DEFAULT_TEXT"],
                        provider="google",
                        input_tokens=getattr(response.usage_metadata, "prompt_token_count", 0) or 0,
                        output_tokens=getattr(response.usage_metadata, "candidates_token_count", 0) or 0,
                        context_type="sales_pitch_generation",
                    )
                )
            except Exception as log_err:
                logger.warning(f"SalesPitchGenerator: Failed to log pitch tokens: {log_err}")

            return {"content": response.text or "AI Error", "references": []}

        except Exception as e:
            logger.error(f"SalesPitchGenerator: Pitch generation failed: {e}")
            try:
                LogService(self.supabase_client).create_log_entry(
                    {
                        "user_input": f"Pitch Request: {company} / {job_title}",
                        "gemini_response": f"AI Error: {str(e)[:500]}",
                        "project_name": "SalesBot",
                        "user_name": "alice@archon.com",
                    }
                )
            except Exception:
                pass
            return {"error_code": 500, "message": str(e)}

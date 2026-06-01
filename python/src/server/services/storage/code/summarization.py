"""
AI Summarization Engine for Code Storage Service (Phase 4.6.12 Hardening)

Handles LLM-powered summary generation and action-oriented naming
for extracted code blocks.
"""

import asyncio
import json
import os
from typing import Any, cast

from src.server.config.logfire_config import search_logger


def _get_model_choice_logic() -> str:
    """Get MODEL_CHOICE with direct fallback from credentials or environment."""
    try:
        from src.server.services.credential_service import credential_service

        if credential_service._cache_initialized and "MODEL_CHOICE" in credential_service._cache:
            model = credential_service._cache["MODEL_CHOICE"]
        else:
            model = os.getenv("MODEL_CHOICE")
            if not model:
                raise ValueError("MODEL_CHOICE is not configured in environment or credentials")
        return cast(str, model)
    except Exception as e:
        search_logger.error(f"Error getting model choice logic: {e}")
        raise


def generate_code_example_summary_logic(
    code: str,
    context_before: str,
    context_after: str,
    language: str = "",
    provider: str | None = None,
) -> dict[str, str]:
    """
    Generate a summary and name for a code example using its surrounding context.
    """
    model_choice = _get_model_choice_logic()

    prompt = f"""<context_before>
{context_before[-500:] if len(context_before) > 500 else context_before}
</context_before>

<code_example language="{language}">
{code[:1500] if len(code) > 1500 else code}
</code_example>

<context_after>
{context_after[:500] if len(context_after) > 500 else context_after}
</context_after>

Based on the code example and its surrounding context, provide:
1. A concise, action-oriented name (1-4 words) that describes what this code DOES.
2. A summary (2-3 sentences) that describes what this code example demonstrates.

Format your response as JSON:
{{
  "example_name": "Action-oriented name",
  "summary": "Description"
}}
"""

    try:
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            from src.server.services.credential_service import credential_service

            if credential_service._cache_initialized and "OPENAI_API_KEY" in credential_service._cache:
                cached_key = credential_service._cache["OPENAI_API_KEY"]
                if isinstance(cached_key, dict) and cached_key.get("is_encrypted"):
                    from src.server.services.credentials.crypto_utils import CryptoUtils

                    api_key = CryptoUtils.decrypt_value(cached_key["encrypted_value"])
                else:
                    api_key = cached_key
            else:
                api_key = os.getenv("OPENAI_API_KEY", "")

        if not api_key:
            raise ValueError("No OpenAI API key available for code summarization")

        client = openai.OpenAI(api_key=api_key)

        from src.server.services.prompt_service import prompt_service
        default_instruction = "You are a helpful assistant that analyzes code examples."
        system_prompt = prompt_service.get_prompt("CODE_EXAMPES_AUDITOR", default=default_instruction)

        response = client.chat.completions.create(
            model=model_choice,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        raw_content = response.choices[0].message.content
        response_content = raw_content.strip() if raw_content is not None else ""
        if not response_content:
            raise ValueError("LLM returned empty summary")

        result = json.loads(response_content)
        return {
            "example_name": result.get(
                "example_name",
                f"Code Example ({language})" if language else "Code Example",
            ),
            "summary": result.get("summary", "Code example for demonstration purposes."),
        }

    except Exception as e:
        search_logger.error(f"Summarization AI Error: {e}")
        return {
            "example_name": (f"Code Example ({language})" if language else "Code Example"),
            "summary": "Code example for demonstration purposes.",
        }


async def generate_code_summaries_batch_logic(
    service_instance,
    code_blocks: list[dict[str, Any]],
    max_workers: int | None = None,
    progress_callback: Any = None,
    provider: str | None = None,
) -> list[dict[str, str]]:
    """
    Generate summaries for a batch of code blocks concurrently.
    """
    if not code_blocks:
        return []

    # Get max_workers from settings if not provided
    if max_workers is None:
        try:
            from src.server.services.credential_service import credential_service

            if credential_service._cache_initialized and "CODE_SUMMARY_MAX_WORKERS" in credential_service._cache:
                max_workers = int(credential_service._cache["CODE_SUMMARY_MAX_WORKERS"])
            else:
                max_workers = int(os.getenv("CODE_SUMMARY_MAX_WORKERS", "3"))
        except Exception:
            max_workers = 3

    search_logger.info(f"Generating summaries for {len(code_blocks)} code blocks with max_workers={max_workers}")

    # Semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_workers)
    completed_count = 0
    lock = asyncio.Lock()

    async def _sum_single(block: dict[str, Any]) -> dict[str, str]:
        nonlocal completed_count
        async with semaphore:
            # CPU/IO intensive LLM call to thread
            result = await asyncio.to_thread(
                generate_code_example_summary_logic,
                code=block["code"],
                context_before=block.get("context_before", ""),
                context_after=block.get("context_after", ""),
                language=block.get("language", ""),
                provider=provider,
            )
            async with lock:
                completed_count += 1
                if progress_callback:
                    await progress_callback(
                        {
                            "status": "code_summarization",
                            "log": f"Generated {completed_count}/{len(code_blocks)} code summaries",
                        }
                    )
            return result

    tasks = [_sum_single(block) for block in code_blocks]
    results = await asyncio.gather(*tasks)
    return list(results)

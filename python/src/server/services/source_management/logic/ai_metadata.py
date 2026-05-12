"""
AI Metadata Logic for Source Management
Physically isolated to reduce monolithic file size.
"""

from typing import Any

from server.config.logfire_config import search_logger
from server.services.llm_provider_service import get_llm_client


async def extract_source_summary(
    source_id: str, content: str, max_length: int = 500, provider: str | None = None
) -> str:
    """Uses LLM to generate a concise summary of source content."""
    default_summary = f"Content from {source_id}"
    if not content or len(content.strip()) == 0:
        return default_summary

    truncated_content = content[:25000] if len(content) > 25000 else content
    prompt = f"""<source_content>
{truncated_content}
</source_content>

The above content is from the documentation for '{source_id}'. Please provide a concise summary (3-5 sentences) that describes what this library/tool/framework is about. The summary should help understand what the library/tool/framework accomplishes and the purpose."""

    try:
        async with get_llm_client(provider=provider) as client:
            from server.services.credential_service import credential_service

            rag_settings = await credential_service.get_credentials_by_category("rag_strategy")
            model_choice = rag_settings.get("MODEL_CHOICE")
            if not model_choice:
                raise ValueError("MODEL_CHOICE is not configured in rag_strategy settings")
            search_logger.info(f"Generating summary for {source_id} using model: {model_choice}")

            response = await client.chat.completions.create(
                model=model_choice,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that provides concise library/tool/framework summaries.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            if not response or not response.choices:
                search_logger.error(f"Empty or invalid response from LLM for {source_id}")
                return default_summary

            msg_content = response.choices[0].message.content
            if msg_content is None:
                search_logger.error(f"LLM returned None content for {source_id}")
                return default_summary

            summary = str(msg_content).strip()
            if len(summary) > max_length:
                return summary[:max_length] + "..."
            return summary
    except Exception as e:
        search_logger.error(f"Error generating summary with LLM for {source_id}: {e}. Using default.")
        return default_summary


async def generate_source_title_and_metadata(
    source_id: str,
    content: str,
    knowledge_type: str = "technical",
    tags: list[str] | None = None,
    provider: str | None = None,
    original_url: str | None = None,
    source_display_name: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Generates a user-friendly title and metadata using LLM."""
    title = source_id
    if content and len(content.strip()) > 100:
        try:
            async with get_llm_client(provider=provider) as client:
                from server.services.credential_service import credential_service

                rag_settings = await credential_service.get_credentials_by_category("rag_strategy")
                model_choice = rag_settings.get("MODEL_CHOICE", "gpt-4.1-nano")
                sample_content = content[:3000]
                source_context = source_display_name or source_id

                source_type_info = ""
                if original_url:
                    if "llms.txt" in original_url:
                        source_type_info = " (detected from llms.txt file)"
                    elif "sitemap" in original_url:
                        source_type_info = " (detected from sitemap)"
                    elif any(d in original_url for d in ["docs", "documentation", "api"]):
                        source_type_info = " (detected from documentation site)"
                    else:
                        source_type_info = " (detected from website)"

                prompt = f"""You are creating a title for crawled content that identifies the SERVICE NAME and SOURCE TYPE.

Source ID: {source_id}
Original URL: {original_url or "Not provided"}
Display Name: {source_context}
{source_type_info}

Content sample:
{sample_content}

Generate a title in this format: "[Service Name] [Source Type]"
Generate only the title, nothing else."""

                response = await client.chat.completions.create(
                    model=model_choice,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates concise titles."},
                        {"role": "user", "content": prompt},
                    ],
                )
                generated_title = response.choices[0].message.content.strip().strip("\"'")
                if len(generated_title) < 50:
                    title = generated_title
        except Exception as e:
            search_logger.error(f"Error generating title for {source_id}: {e}")

    metadata = {"knowledge_type": knowledge_type, "tags": tags or [], "source_type": "url", "auto_generated": True}
    return title, metadata

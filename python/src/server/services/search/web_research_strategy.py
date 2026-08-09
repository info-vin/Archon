import logging
from typing import Any

from ...utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


async def perform_web_research_impl(query: str, genai_module: Any, types_module: Any) -> tuple[str, str]:
    """
    Executes Google Search Grounding via Gemini.
    Returns (content, source_id).
    """
    try:
        from ..credential_service import credential_service
        from ..librarian_service import LibrarianService

        api_key = await credential_service.get_credential("GEMINI_API_KEY")
        if not api_key:
            api_key = await credential_service.get_credential("GOOGLE_API_KEY")

        if not api_key:
            logger.warning("No GEMINI_API_KEY found for web research")
            return "", ""

        client = genai_module.Client(api_key=api_key)
        google_search_tool = types_module.Tool(google_search=types_module.GoogleSearch())

        prompt = f"""
        Research the following query and provide a comprehensive summary.
        Focus on factual, up-to-date information.

        Query: {query}
        """

        from ...config.model_ssot import SYSTEM_MODELS

        model_id = SYSTEM_MODELS["DEFAULT_TEXT"]

        @retry_with_backoff(max_retries=2)
        async def _call_gemini() -> Any:
            return await client.aio.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types_module.GenerateContentConfig(
                    tools=[google_search_tool],
                    response_modalities=["TEXT"],
                ),
            )

        response = await _call_gemini()

        content = ""
        references = []

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.text:
                    content += part.text

        if (
            response.candidates
            and response.candidates[0].grounding_metadata
            and response.candidates[0].grounding_metadata.grounding_chunks
        ):
            for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
                if chunk.web and chunk.web.uri:
                    references.append(chunk.web.uri)

        if not content:
            logger.warning("Web research returned empty content")
            return "", ""

        librarian = LibrarianService()
        source_id = await librarian.archive_web_research(query, content, references)

        return content, source_id

    except Exception as e:
        logger.error(f"Error performing web research: {e}")
        return "", ""

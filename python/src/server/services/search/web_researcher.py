# python/src/server/services/search/web_researcher.py
import logging
from google import genai
from google.genai import types
from ...config.logfire_config import get_logger
from ...config.model_ssot import SYSTEM_MODELS

logger = get_logger("web_researcher")

# EXPORT FOR TEST PATCHING
Client = genai.Client

class WebResearcher:
    """Independent Web Research Module (Decoupled Phase 4.6.47)."""

    @staticmethod
    async def perform_web_research(query: str) -> tuple[str, str]:
        try:
            from ..credential_service import credential_service
            from ..librarian_service import LibrarianService

            api_key = await credential_service.get_credential("GEMINI_API_KEY")
            if not api_key:
                return "", ""

            client = genai.Client(api_key=api_key)
            google_search_tool = types.Tool(google_search=types.GoogleSearch())
            
            response = client.models.generate_content(
                model=SYSTEM_MODELS["DEFAULT_TEXT"],
                contents=f"Research: {query}",
                config=types.GenerateContentConfig(tools=[google_search_tool], response_modalities=["TEXT"]),
            )

            content = ""
            if response.candidates:
                content = "".join([p.text for p in response.candidates[0].content.parts if p.text])
            
            if not content:
                return "", ""

            source_id = await LibrarianService().archive_web_research(query, content, [])
            return content, source_id
        except Exception as e:
            logger.error(f"Web research failed: {e}")
            return "", ""

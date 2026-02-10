from typing import Any, cast

from ..config.logfire_config import get_logger, safe_logfire_error, safe_logfire_info
from ..utils import get_supabase_client
from ..utils.json_utils import safe_json_loads
from .crawler_manager import get_crawler
from .llm_provider_service import extract_message_text, get_llm_client

logger = get_logger(__name__)

class ExtractionService:
    """
    Service for managing data extraction schemas and analyzing web content structure.
    Integrates with LLM to auto-discover potential fields from raw web content.
    """

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client or get_supabase_client()

    async def analyze_url_structure(self, url: str) -> dict[str, Any]:
        """
        Crawls a URL and uses LLM to analyze its structure, suggesting potential fields.
        """
        safe_logfire_info(f"Analyzing structure for URL: {url}")

        # 1. Fetch content (Lightweight fetch)
        content = ""
        try:
            crawler = await get_crawler()
            if not crawler:
                raise Exception("Crawler unavailable")

            # Use crawl4ai to get markdown directly
            result = await crawler.arun(url)
            content = result.markdown

            # Truncate content to avoid context limit issues
            if len(content) > 15000:
                content = content[:15000] + "...(truncated)"

        except Exception as e:
            safe_logfire_error(f"Failed to crawl URL for analysis: {e}")
            raise Exception(f"Failed to fetch content: {str(e)}") from e

        # 2. Analyze with LLM
        try:
            system_prompt = (
                "You are a Data Extraction Expert. Analyze the provided web content (Markdown) "
                "and identify key structured data fields that would be valuable for business intelligence "
                "(Sales, Marketing, HR). \n"
                "Return a JSON object with a 'fields' list. Each field should have: 'name', 'type' (string, number, list), "
                "and 'description' (example value from text)."
            )

            user_prompt = f"Analyze this content:\n\n{content}"

            async with get_llm_client() as client:
                response = await client.chat.completions.create(
                    model="gemini-1.5-flash", # Use a stable default
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"}
                )

                # Extract text using utility
                content_text, _, _ = extract_message_text(response.choices[0])
                schema_suggestion = safe_json_loads(content_text)
                return schema_suggestion

        except Exception as e:
            safe_logfire_error(f"LLM analysis failed: {e}")
            raise Exception(f"AI Analysis failed: {str(e)}") from e

    async def create_schema(self, data: dict[str, Any], user_id: str) -> dict[str, Any]:
        """
        Creates a new extraction schema definition.
        """
        try:
            payload = {
                "name": data["name"],
                "domain_pattern": data["domain_pattern"],
                "schema_definition": data["schema_definition"],
                "target_role": data.get("target_role"),
                "description": data.get("description"),
                "created_by": user_id
            }

            response = self.supabase.table("archon_extraction_schemas").insert(payload).execute()

            if not response.data:
                raise Exception("Insert failed")

            return cast(dict[str, Any], response.data[0])

        except Exception as e:
            safe_logfire_error(f"Failed to create schema: {e}")
            raise

    async def list_schemas(self) -> list[dict[str, Any]]:
        """List all schemas."""
        response = self.supabase.table("archon_extraction_schemas").select("*").order("created_at", desc=True).execute()
        return cast(list[dict[str, Any]], response.data or [])

    async def delete_schema(self, schema_id: str) -> bool:
        """Delete a schema."""
        self.supabase.table("archon_extraction_schemas").delete().eq("id", schema_id).execute()
        return True

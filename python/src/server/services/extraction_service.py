from typing import Any, cast

from ..config.logfire_config import get_logger, safe_logfire_error, safe_logfire_info
from ..config.model_ssot import SYSTEM_MODELS
from ..utils import get_supabase_client
from ..utils.json_utils import safe_json_loads
from .crawler_manager import get_crawler
from .llm_provider_service import extract_message_text

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
            # Normalize URL (add https:// if missing)
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"

            from crawl4ai import AsyncWebCrawler, BrowserConfig
            browser_config = BrowserConfig(
                headless=True,
                verbose=False,
                browser_type="chromium",
                extra_args=["--no-sandbox"],
            )
            async with AsyncWebCrawler(config=browser_config) as crawler:
                # Use crawl4ai to get markdown directly
                result = await crawler.arun(url)
                content = result.markdown if hasattr(result, "markdown") and result.markdown else ""

                if not content:
                    # Fallback: Try raw HTML if markdown extraction failed
                    content = result.html if hasattr(result, "html") and result.html else ""

                if not content:
                    error_msg = getattr(result, "error_message", "No error message")
                    raise Exception(f"URL returned empty content. Status: {getattr(result, 'status_code', 'unknown')}. Error: {error_msg}")

            # Truncate content to avoid context limit issues
            if len(content) > 15000:
                content = content[:15000] + "...(truncated)"

        except Exception as e:
            safe_logfire_error(f"Failed to crawl URL for analysis: {e}")
            raise Exception(f"Failed to fetch content: {str(e)}") from e

        # 2. Analyze with LLM
        try:
            from .prompt_service import prompt_service

            default_prompt = (
                "You are a Data Extraction Expert. Analyze the provided web content (Markdown) "
                "and identify key structured data fields that would be valuable for business intelligence "
                "(Sales, Marketing, HR). \n"
                "Return a JSON object with: \n"
                "1. 'summary': A 2-3 sentence semantic understanding of what this website is and its main business purpose.\n"
                "2. 'fields': A list where each field has: 'name', 'type' (string, number, list), "
                "and 'description' (example value from text)."
            )
            system_prompt = prompt_service.get_prompt("data_extraction_prompt", default_prompt)

            user_prompt = f"Analyze this content:\n\n{content}"

            # Phase 4.7 Optimization: Use standard LLM client pattern
            from ..config.model_ssot import SYSTEM_MODELS
            from .llm_provider_service import get_llm_client

            async with get_llm_client() as client:
                # Use Gemini 2.0 Flash for stability and long context
                response = await client.chat.completions.create(
                    model=SYSTEM_MODELS["DEFAULT_TEXT"],
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    response_format={"type": "json_object"},
                )

                # Extract text using utility
                content_text, _, _ = extract_message_text(response.choices[0])
                schema_suggestion = safe_json_loads(content_text)
                return schema_suggestion

        except Exception as e:
            safe_logfire_error(f"LLM analysis failed: {e}")
            # Fallback: Return a generic schema suggestion instead of crashing
            return {
                "fields": [
                    {"name": "title", "type": "string", "description": "Page Title or Main Heading"},
                    {"name": "summary", "type": "string", "description": "Brief summary of the content"},
                    {"name": "url", "type": "string", "description": "Source URL"},
                    {"name": "author", "type": "string", "description": "Content creator or organization"},
                    {"name": "published_date", "type": "string", "description": "Date of publication"},
                ],
                "error": f"AI Analysis failed, using fallback. Reason: {str(e)[:100]}",
            }

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
                "created_by": user_id,
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

    async def get_schema(self, schema_id: str) -> dict[str, Any] | None:
        """Get a single schema by ID."""
        response = self.supabase.table("archon_extraction_schemas").select("*").eq("id", schema_id).execute()
        return response.data[0] if response.data else None

    async def update_schema(self, schema_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Updates an existing schema."""
        update_data = {
            k: v
            for k, v in data.items()
            if k in ["name", "domain_pattern", "schema_definition", "target_role", "description"]
        }
        response = self.supabase.table("archon_extraction_schemas").update(update_data).eq("id", schema_id).execute()
        if not response.data:
            raise Exception("Update failed or schema not found")
        return cast(dict[str, Any], response.data[0])

    async def delete_schema(self, schema_id: str) -> bool:
        """Delete a schema."""
        self.supabase.table("archon_extraction_schemas").delete().eq("id", schema_id).execute()
        return True

    async def run_extraction(self, url: str, schema_id: str, user_id: str) -> dict[str, Any]:
        """
        Performs actual data extraction: Crawl -> LLM Parse (using schema) -> Result.
        """
        safe_logfire_info(f"User {user_id} triggered real extraction for {url} using schema {schema_id}")

        # 1. Get the Schema
        schema = await self.get_schema(schema_id)
        if not schema:
            raise Exception(f"Schema {schema_id} not found")

        # 2. Fetch Content
        crawler = await get_crawler()
        if not crawler:
            raise Exception("Crawler unavailable")
        result = await crawler.arun(url)
        content = result.markdown if hasattr(result, "markdown") and result.markdown else ""
        if not content:
            raise Exception("Failed to crawl content for extraction")

        # 3. Extract with LLM using the schema definition
        from .llm_provider_service import get_llm_client

        schema_json = schema["schema_definition"]
        system_prompt = (
            f"You are a Data Extraction Expert. Extract structured data from the provided content "
            f"strictly following this JSON schema: {schema_json}. \n"
            "Return only the extracted data as a JSON object."
        )

        async with get_llm_client() as client:
            response = await client.chat.completions.create(
                model=SYSTEM_MODELS["DEFAULT_TEXT"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract data from this content:\n\n{content[:15000]}"},
                ],
                response_format={"type": "json_object"},
            )

            content_text, _, _ = extract_message_text(response.choices[0])
            extracted_data = safe_json_loads(content_text)

            # 4. Persistence (Physical Log)
            # In a full Phase 5 implementation, this would go to archon_extracted_data.
            # For 4.6.23, we log the success and return the data to fulfill the loop.
            logger.info(f"Successfully extracted data from {url} using schema '{schema['name']}'")

            return {"success": True, "data": extracted_data, "schema_used": schema["name"], "source_url": url}

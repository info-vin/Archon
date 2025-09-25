from ..utils import get_supabase_client
from ..config.logfire_config import get_logger, safe_logfire_info

logger = get_logger(__name__)

class KnowledgeService:
    def __init__(self):
        self.supabase = get_supabase_client()

    async def get_code_examples(self, source_id: str) -> list[dict]:
        """Retrieves all code examples for a specific knowledge item."""
        try:
            safe_logfire_info(f"Fetching code examples for source_id: {source_id}")

            result = (
                self.supabase.from_("archon_code_examples")
                .select("id, source_id, content, summary, metadata")
                .eq("source_id", source_id)
                .execute()
            )

            code_examples = result.data if isinstance(result.data, list) else []
            safe_logfire_info(f"Found {len(code_examples)} code examples for {source_id}")
            return code_examples
        except Exception as e:
            logger.error(f"Failed to fetch code examples from database | error={str(e)} | source_id={source_id}")
            return []

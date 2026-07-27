"""
Base Search Strategy

Implements the foundational vector similarity search that all other strategies build upon.
This is the core semantic search functionality.
"""

from typing import Any

from supabase import Client

from src.server.repositories.base_repository import BaseRepository

from ...config.logfire_config import get_logger, safe_span

logger = get_logger(__name__)

# Default similarity threshold for vector results
SIMILARITY_THRESHOLD = 0.30


class BaseSearchStrategy(BaseRepository):
    """Base strategy implementing fundamental vector similarity search"""

    def __init__(self, supabase_client: Client):
        """Initialize with database client"""
        super().__init__(supabase_client)

    async def get_dynamic_threshold(self) -> float:
        """Fetch dynamic threshold from settings with fallback to SIMILARITY_THRESHOLD"""
        try:
            # Avoid querying mock client in unit tests to prevent mock state pollution
            if type(self.supabase_client).__name__ in ("MagicMock", "Mock"):
                return SIMILARITY_THRESHOLD

            # Try to fetch RAG_SIMILARITY_THRESHOLD from archon_settings
            query = self.supabase_client.table("archon_settings").select("value").eq("key", "RAG_SIMILARITY_THRESHOLD")
            success, result = self.execute_query(
                query.execute,
                error_context="Error fetching dynamic RAG similarity threshold",
                require_data=False
            )
            if success and result and isinstance(result.get("data"), list) and len(result["data"]) > 0:
                val = result["data"][0].get("value")
                if val is not None and not hasattr(val, "_mock_return_value"):
                    return float(val)
        except Exception:
            pass
        return SIMILARITY_THRESHOLD

    async def vector_search(
        self,
        query_embedding: list[float],
        match_count: int,
        filter_metadata: dict | None = None,
        table_rpc: str = "match_archon_crawled_pages",
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform basic vector similarity search.

        This is the foundational semantic search that all strategies use.

        Args:
            query_embedding: The embedding vector for the query
            match_count: Number of results to return
            filter_metadata: Optional metadata filters
            table_rpc: The RPC function to call (match_archon_crawled_pages or match_archon_code_examples)
            min_score: Optional minimum similarity threshold to override default

        Returns:
            List of matching documents with similarity scores
        """
        with safe_span("base_vector_search", table=table_rpc, match_count=match_count) as span:
            # Determine threshold
            if min_score is not None:
                threshold = min_score
            else:
                threshold = await self.get_dynamic_threshold()

            # Build RPC parameters
            rpc_params = {"query_embedding": query_embedding, "match_count": match_count}

            # Add filter parameters
            if filter_metadata:
                if "source" in filter_metadata:
                    rpc_params["source_filter"] = filter_metadata["source"]
                    rpc_params["filter"] = {}
                else:
                    rpc_params["filter"] = filter_metadata
            else:
                rpc_params["filter"] = {}

            # Execute search
            query = self.supabase_client.rpc(table_rpc, rpc_params)
            success, response = self.execute_query(query, error_context=f"Vector search failed ({table_rpc})")

            if not success:
                span.set_attribute("error", str(response.get("error")))
                return []

            # Filter by similarity threshold
            filtered_results = []
            data = response.get("data", [])
            if data:
                for result in data:
                    similarity = float(result.get("similarity") or 0.0)
                    if similarity >= threshold:
                        # Physical Hardening: Ensure content is clean UTF-8 string
                        content = result.get("content", "")
                        if content and isinstance(content, str):
                            try:
                                # Fix potential Latin-1/UTF-8 double-encoding/mismatch
                                result["content"] = content.encode("latin-1").decode("utf-8")
                            except (UnicodeEncodeError, UnicodeDecodeError):
                                # Already healthy or unfixable
                                pass
                        filtered_results.append(result)

            span.set_attribute("results_found", len(filtered_results))
            span.set_attribute(
                "results_filtered",
                len(data) - len(filtered_results) if data else 0,
            )

            return filtered_results

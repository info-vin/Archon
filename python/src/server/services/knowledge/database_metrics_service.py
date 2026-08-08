"""
Database Metrics Service

Handles retrieval of database statistics and metrics.
"""

from datetime import datetime
from typing import Any

from ...config.logfire_config import safe_logfire_error, safe_logfire_info
from ...repositories.base_repository import BaseRepository


class DatabaseMetricsService(BaseRepository):
    """
    Service for retrieving database metrics and statistics.
    """

    def __init__(self, supabase_client: Any = None) -> None:
        """
        Initialize the database metrics service.

        Args:
            supabase_client: The Supabase client for database operations
        """
        super().__init__(supabase_client)
        self.supabase = self.supabase_client

    async def get_metrics(self) -> dict[str, Any]:
        """
        Get database metrics and statistics.

        Returns:
            Dictionary containing database metrics
        """
        try:
            safe_logfire_info("Getting database metrics")

            # Get counts from various tables
            metrics = {}

            # Sources count
            success1, sources_result = self.execute_query(self.supabase.table("archon_sources").select("*", count="exact"), "Get sources count") # 合法
            metrics["sources_count"] = sources_result.get("count", 0) if success1 else 0

            # Crawled pages count
            success2, pages_result = self.execute_query(self.supabase.table("archon_crawled_pages").select("*", count="exact"), "Get pages count") # 合法
            metrics["pages_count"] = pages_result.get("count", 0) if success2 else 0

            # Code examples count
            try:
                success3, code_examples_result = self.execute_query(self.supabase.table("archon_code_examples").select("*", count="exact"), "Get code examples count") # 合法
                metrics["code_examples_count"] = code_examples_result.get("count", 0) if success3 else 0
            except Exception:
                metrics["code_examples_count"] = 0

            # Add timestamp
            metrics["timestamp"] = datetime.now().isoformat()

            # Calculate additional metrics
            metrics["average_pages_per_source"] = (
                round(metrics["pages_count"] / metrics["sources_count"], 2) if metrics["sources_count"] > 0 else 0
            )

            safe_logfire_info(
                f"Database metrics retrieved | sources={metrics['sources_count']} | pages={metrics['pages_count']} | code_examples={metrics['code_examples_count']}"
            )

            return metrics

        except Exception as e:
            safe_logfire_error(f"Failed to get database metrics | error={str(e)}")
            raise

    async def get_storage_statistics(self) -> dict[str, Any]:
        """
        Get storage statistics including sizes and counts by type.

        Returns:
            Dictionary containing storage statistics
        """
        try:
            stats: dict[str, Any] = {}

            # Get knowledge type distribution
            success, knowledge_types_result = self.execute_query(self.supabase.table("archon_sources").select("metadata->knowledge_type"), "Get knowledge type distribution") # 合法

            if success and knowledge_types_result.get("data"):
                type_counts: dict[str, int] = {}
                for row in knowledge_types_result["data"]:
                    ktype = row.get("knowledge_type", "unknown")
                    type_counts[ktype] = type_counts.get(ktype, 0) + 1
                stats["knowledge_type_distribution"] = type_counts

            # Get recent activity
            success, recent_sources = self.execute_query(
                self.supabase.table("archon_sources") # 合法
                .select("source_id, created_at")
                .order("created_at", desc=True)
                .limit(5),
                "Get recent activity"
            )

            stats["recent_sources"] = [
                {"source_id": s["source_id"], "created_at": s["created_at"]} for s in (recent_sources.get("data", []) if success else [])
            ]

            return stats

        except Exception as e:
            safe_logfire_error(f"Failed to get storage statistics | error={str(e)}")
            return {}

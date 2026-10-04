"""
Database Metrics Service

Handles retrieval of database statistics and metrics.
"""

from datetime import datetime
from typing import TypedDict

from supabase import Client

from ...config.logfire_config import safe_logfire_error, safe_logfire_info
from ...repositories.base_repository import BaseRepository


class DatabaseMetricsDTO(TypedDict):
    sources_count: int
    pages_count: int
    code_examples_count: int
    timestamp: str
    average_pages_per_source: float


class RecentSourceDTO(TypedDict):
    source_id: str
    created_at: str


class StorageStatisticsDTO(TypedDict):
    knowledge_type_distribution: dict[str, int]
    recent_sources: list[RecentSourceDTO]


class DatabaseMetricsService(BaseRepository):
    """
    Service for retrieving database metrics and statistics.
    """

    def __init__(self, supabase_client: Client | None = None) -> None:
        """
        Initialize the database metrics service.

        Args:
            supabase_client: The Supabase client for database operations
        """
        super().__init__(supabase_client)
        self.supabase = self.supabase_client

    async def get_metrics(self) -> DatabaseMetricsDTO:
        """
        Get database metrics and statistics.

        Returns:
            DatabaseMetricsDTO containing database metrics
        """
        try:
            safe_logfire_info("Getting database metrics")

            if self.supabase is None:
                raise ValueError("Supabase client is not initialized")

            # Sources count
            success1, sources_result = self.execute_query(
                self.supabase.table("archon_sources").select("*", count="exact"),
                "Get sources count",
            )
            sources_count = (
                sources_result.get("count", 0) if (success1 and sources_result) else 0
            )

            # Crawled pages count
            success2, pages_result = self.execute_query(
                self.supabase.table("archon_crawled_pages").select("*", count="exact"),
                "Get pages count",
            )
            pages_count = (
                pages_result.get("count", 0) if (success2 and pages_result) else 0
            )

            # Code examples count
            try:
                success3, code_examples_result = self.execute_query(
                    self.supabase.table("archon_code_examples").select(
                        "*", count="exact"
                    ),
                    "Get code examples count",
                )
                code_examples_count = (
                    code_examples_result.get("count", 0)
                    if (success3 and code_examples_result)
                    else 0
                )
            except Exception:
                code_examples_count = 0

            # Calculate additional metrics
            average_pages = (
                round(pages_count / sources_count, 2) if sources_count > 0 else 0.0
            )
            timestamp_str = datetime.now().isoformat()

            safe_logfire_info(
                f"Database metrics retrieved | sources={sources_count} | pages={pages_count} | code_examples={code_examples_count}"
            )

            return DatabaseMetricsDTO(
                sources_count=sources_count,
                pages_count=pages_count,
                code_examples_count=code_examples_count,
                timestamp=timestamp_str,
                average_pages_per_source=average_pages,
            )

        except Exception as e:
            safe_logfire_error(f"Failed to get database metrics | error={str(e)}")
            raise

    async def get_storage_statistics(self) -> StorageStatisticsDTO:
        """
        Get storage statistics including sizes and counts by type.

        Returns:
            StorageStatisticsDTO containing storage statistics
        """
        try:
            if self.supabase is None:
                raise ValueError("Supabase client is not initialized")

            type_counts: dict[str, int] = {}
            recent_sources_list: list[RecentSourceDTO] = []

            # Get knowledge type distribution
            success, knowledge_types_result = self.execute_query(
                self.supabase.table("archon_sources").select(
                    "metadata->knowledge_type"
                ),
                "Get knowledge type distribution",
            )

            if success and knowledge_types_result and knowledge_types_result.get("data"):
                for row in knowledge_types_result["data"]:
                    ktype = row.get("knowledge_type", "unknown") if isinstance(row, dict) else "unknown"
                    type_counts[ktype] = type_counts.get(ktype, 0) + 1

            # Get recent activity
            success, recent_sources = self.execute_query(
                self.supabase.table("archon_sources")
                .select("source_id, created_at")
                .order("created_at", desc=True)
                .limit(5),
                "Get recent activity",
            )

            if success and recent_sources and recent_sources.get("data"):
                for s in recent_sources["data"]:
                    if isinstance(s, dict) and "source_id" in s and "created_at" in s:
                        recent_sources_list.append(
                            RecentSourceDTO(
                                source_id=str(s["source_id"]),
                                created_at=str(s["created_at"]),
                            )
                        )

            return StorageStatisticsDTO(
                knowledge_type_distribution=type_counts,
                recent_sources=recent_sources_list,
            )

        except Exception as e:
            safe_logfire_error(f"Failed to get storage statistics | error={str(e)}")
            return StorageStatisticsDTO(
                knowledge_type_distribution={},
                recent_sources=[],
            )

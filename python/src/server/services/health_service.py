# python/src/server/services/health_service.py

import datetime
import json
from typing import Any, NotRequired, TypedDict

from src.server.repositories.base_repository import BaseRepository

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client
from .search.rag_service import RAGService


class HealthScoreDetails(TypedDict):
    error: NotRequired[str]
    alignment_raw: NotRequired[float]
    db_connected: NotRequired[bool]
    search_active: NotRequired[bool]
    total_sources: NotRequired[int]
    indexed_sources: NotRequired[int]
    timestamp: NotRequired[str]


class HealthStatusResult(TypedDict):
    status: str
    score: float
    details: HealthScoreDetails


class TrendEntry(TypedDict):
    date: str
    score: float


class HealthHistoryResult(TypedDict):
    trend: list[TrendEntry]
    audit: list[dict[str, Any]]

logger = get_logger(__name__)


class HealthService(BaseRepository):
    """
    Service for checking the health of system components including the database.
    """

    def __init__(self, supabase_client=None):
        super().__init__(supabase_client or get_supabase_client())

    def check_db_health(self) -> bool:
        """Checks if the database is reachable and responding."""

        def _query():
            return self.supabase_client.table("profiles").select("id", count="exact").limit(1).execute()

        success, _ = self.execute_query(_query, "DB health check failed")
        return success

    def verify_auth_config(self) -> bool:
        """Verifies if the Supabase Auth configuration is valid."""
        try:
            # Minimal check to see if auth client is initialized
            return self.supabase_client.auth is not None
        except Exception:
            return False

    async def check_rag_integrity(self) -> HealthStatusResult:
        """
        Performs a deep integrity check of the RAG system.
        Calculates a weighted System Integrity Score without polluting the DB.
        Weightage: Knowledge Alignment (70%) + DB (15%) + Search (15%)
        """
        logger.info("📊 Calculating Composite System Integrity Score (Read-Only)...")

        # 1. DB Connectivity Check (15% weight)
        db_ok = self.check_db_health()
        db_score = 15.0 if db_ok else 0.0

        if not db_ok:
            return {"status": "unhealthy", "score": 0.0, "details": {"error": "Critical: Database connection lost."}}

        # 2. Knowledge Alignment Check (70% weight)
        def _query_sources():
            return self.supabase_client.table("archon_sources").select("source_id", count="exact").execute()

        success, res = self.execute_query(_query_sources, "Error counting sources", require_data=False)
        if not success:
            logger.error("💥 System Integrity Calculation Failed")
            return {"status": "unhealthy", "score": 0.0, "details": {"error": str(res.get("error") or "Unknown database error")}}

        # res['count'] is populated by BaseRepository.execute_query
        total_count = int(res.get("count") or 0)
        data = res.get("data")
        if total_count == 0 and isinstance(data, list):
            total_count = len(data)

        alignment_score = 0.0
        indexed_count = 0
        if total_count > 0:

            def _query_indexed():
                return (
                    self.supabase_client.table("archon_crawled_pages")
                    .select("source_id", count="exact")
                    .not_.is_("embedding", "null")
                    .execute()
                )

            idx_success, idx_res = self.execute_query(
                _query_indexed, "Error counting indexed sources", require_data=False
            )
            if idx_success:
                idx_data = idx_res.get("data") or []
                # Count the number of unique source_ids that have active crawled pages
                indexed_count = len({row["source_id"] for row in idx_data})

                alignment_score = (indexed_count / total_count) * 70.0
        else:
            alignment_score = 70.0  # Default full if system is fresh/empty

        # 3. Search Responsiveness Check (15% weight)
        rag = RAGService()
        search_ok = False
        try:
            test_search = await rag.search_documents(query="Archon", match_count=1)
            search_ok = len(test_search) > 0 if isinstance(test_search, list) else False
        except Exception as e:
            logger.error(f"Probe Search Check failed: {e}")
            search_ok = False

        search_score = 15.0 if search_ok else 0.0

        # 4. Composite Score
        final_score = round(db_score + alignment_score + search_score, 2)

        return {
            "status": "healthy" if final_score >= 90 else ("degraded" if final_score >= 70 else "unhealthy"),
            "score": final_score,
            "details": {
                "alignment_raw": round((alignment_score / 70.0) * 100, 1) if total_count > 0 else 100.0,
                "db_connected": db_ok,
                "search_active": search_ok,
                "total_sources": total_count,
                "indexed_sources": indexed_count,
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            },
        }

    async def get_health_history(self, days: int = 30) -> HealthHistoryResult:
        """
        Retrieves historical integrity audit logs from archon_logs table.
        """
        since = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)).isoformat()

        def _query():
            return (
                self.supabase_client.table("archon_logs")
                .select("*")
                .eq("source", "clockwork-scheduler")
                .gt("created_at", since)
                .order("created_at", desc=True)
                .execute()
            )

        success, res = self.execute_query(_query, "History fetch failed", require_data=False)
        if not success:
            return {"trend": [], "audit": []}

        logs = res.get("data") or []
        trend: list[TrendEntry] = []
        audit_trail: list[dict[str, Any]] = []

        for log in logs:
            details = log.get("details", {})
            # Handle if details is a string (JSON string)
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except Exception:
                    details = {}

            score = details.get("score") if isinstance(details, dict) else None

            if score is not None:
                audit_trail.append(log)
                trend.append({"date": log["created_at"][:10], "score": score})

        trend.sort(key=lambda x: x["date"])

        return {"trend": trend, "audit": audit_trail[:10]}

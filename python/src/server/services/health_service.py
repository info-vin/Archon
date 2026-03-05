import datetime

from ..config.logfire_config import get_logger
from ..repositories.base_repository import BaseRepository
from ..utils import get_supabase_client
from .search.rag_service import RAGService

logger = get_logger(__name__)

class HealthService(BaseRepository):
    """Service for checking the health of the application and its dependencies."""

    def __init__(self):
        client = get_supabase_client()
        super().__init__(client)

    def check_database_connection(self) -> bool:
        """Checks if the database connection is active."""
        def _query(): return self.supabase_client.table("profiles").select("id").limit(1).execute()
        success, _ = self.execute_query(query_func=_query, error_context="Database connection check failed", require_data=False)
        return success

    def check_table_existence(self, table_name: str) -> bool:
        """Checks if a specific table exists in the database."""
        def _query(): return self.supabase_client.table(table_name).select("id").limit(1).execute()
        success, _ = self.execute_query(query_func=_query, error_context=f"Table check failed for {table_name}", require_data=False)
        return success

    def get_system_health(self) -> dict:
        """Returns a comprehensive health status of the system."""
        db_connected = self.check_database_connection()

        if not db_connected:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "services": {}
            }

        # Use correct prefixed table names for Archon
        tables_to_check = ["archon_projects", "archon_tasks", "profiles", "archon_settings"]
        table_statuses = {}
        all_tables_ok = True
        for table in tables_to_check:
            exists = self.check_table_existence(table)
            table_statuses[f"{table}_table"] = exists
            if not exists:
                all_tables_ok = False

        system_status = "healthy" if all_tables_ok else "degraded"

        return {
            "status": system_status,
            "database": "connected",
            "services": {
                "schema": {
                    **table_statuses,
                    "valid": all_tables_ok
                }
            }
        }

    async def check_rag_integrity(self) -> dict:
        """
        Calculates a weighted System Integrity Score without polluting the DB.
        Weightage: Knowledge Alignment (70%) + DB (15%) + Search (15%)
        """
        logger.info("📊 Calculating Composite System Integrity Score (Read-Only)...")

        # 1. DB Connectivity Check (15% weight)
        db_ok = self.check_database_connection()
        db_score = 15.0 if db_ok else 0.0

        if not db_ok:
            return {
                "status": "unhealthy",
                "score": 0.0,
                "details": {"error": "Critical: Database connection lost."}
            }

        # 2. Knowledge Alignment Check (70% weight)
        def _query_sources(): return self.supabase_client.table("archon_sources").select("source_id", count="exact").execute()
        success, res = self.execute_query(query_func=_query_sources, error_context="Error counting sources", require_data=False)
        if not success:
            logger.error("💥 System Integrity Calculation Failed formatting total count")
            return {"status": "unhealthy", "score": 0.0, "details": {"error": res["error"]}}

        total_count = res.get("count", 0) or 0

        alignment_score = 0.0
        indexed_count = 0
        if total_count > 0:
            def _query_indexed(): return self.supabase_client.table("archon_crawled_pages").select("source_id").not_.is_("embedding", "null").execute()
            idx_success, idx_res = self.execute_query(query_func=_query_indexed, error_context="Error counting indexed sources", require_data=False)
            if idx_success:
                indexed_count = len({row["source_id"] for row in (idx_res["data"] or [])})
                alignment_score = (indexed_count / total_count) * 70.0
        else:
            alignment_score = 70.0 # Default full if system is fresh/empty

        # 3. Search Responsiveness Check (15% weight)
        rag = RAGService()
        search_ok = False
        try:
            test_search = await rag.search_documents(query="Archon", match_count=1)
            search_ok = len(test_search) > 0
        except Exception:
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
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
            }
        }

    async def get_health_history(self, days: int = 30) -> dict:
        """
        Retrieves historical integrity audit logs from archon_logs table.
        This provides the physical data for the 'System Health Audit Trail' in Nexus.
        """
        since = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)).isoformat()

        def _query():
            return self.supabase_client.table("archon_logs")\
                .select("*")\
                .eq("source", "clockwork-scheduler")\
                .gt("created_at", since)\
                .order("created_at", desc=True)\
                .execute()

        success, res = self.execute_query(query_func=_query, error_context="History fetch failed", require_data=False)
        if not success:
            logger.error("HealthService: History fetch failed")
            return {"trend": [], "audit": []}

        logs = res["data"] or []
        trend = []
        audit_trail = []

        for log in logs:
            details = log.get("details", {})
            score = details.get("score") if isinstance(details, dict) else None

            if score is not None:
                audit_trail.append(log)
                trend.append({
                    "date": log["created_at"][:10],
                    "score": score
                })

        trend.sort(key=lambda x: x["date"])

        return {
            "trend": trend,
            "audit": audit_trail[:10]
        }

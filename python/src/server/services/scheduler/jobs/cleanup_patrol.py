"""
Cleanup Patrol for Scheduler
Handles deletion of probe data, stale sources, and orphaned indexes.
"""

from datetime import UTC, datetime, timedelta

from src.server.config.logfire_config import get_logger
from src.server.services.shared_constants import AgentUUIDs

logger = get_logger(__name__)

async def cleanup_system_probes() -> None:
    """Retention Policy: Deletes Probe data older than 48h."""
    logger.info("🧹 Clockwork: Running System Probe Cleanup...")
    try:
        from src.server.repositories.base_repository import BaseRepository
        from src.server.utils import get_supabase_client

        supabase = get_supabase_client()
        repo = BaseRepository(supabase)
        cutoff_time = (datetime.now(UTC) - timedelta(hours=48)).isoformat()

        # 1. Leads cleanup
        success, res = repo.execute_query(
            lambda: supabase.table("leads").delete().eq("company_name", "System Probe").lt("created_at", cutoff_time).execute(), # 合法
            "Cleanup leads"
        )
        deleted_leads = len(res.get("data", []) if success else [])

        # 2. Content pages cleanup
        success, res_pages = repo.execute_query(
            lambda: supabase.table("archon_crawled_pages") # 合法
            .delete()
            .like("source_id", "pitch-systemprobe-%")
            .lt("created_at", cutoff_time)
            .execute(),
            "Cleanup crawled pages"
        )
        deleted_pages = len(res_pages.get("data", []) if success else [])

        # 3. Document versions cleanup
        success, res_versions = repo.execute_query(
            lambda: supabase.table("archon_document_versions") # 合法
            .delete()
            .eq("created_by", AgentUUIDs.LIBRARIAN)
            .like("change_summary", "%System Probe%")
            .lt("created_at", cutoff_time)
            .execute(),
            "Cleanup document versions"
        )
        deleted_versions = len(res_versions.get("data", []) if success else [])

        # 4. Sources cleanup
        success, res_sources = repo.execute_query(
            lambda: supabase.table("archon_sources") # 合法
            .delete()
            .like("source_id", "pitch-systemprobe-%")
            .lt("created_at", cutoff_time)
            .execute(),
            "Cleanup sources"
        )
        deleted_sources = len(res_sources.get("data", []) if success else [])

        # 5. Clean up any orphaned sources in the database (e.g. leftover test files with no vector index)
        deleted_orphans = 0
        try:
            s_succ, sources_res = repo.execute_query(lambda: supabase.table("archon_sources").select("source_id").execute(), "Fetch sources") # 合法
            all_sources = {s["source_id"] for s in (sources_res.get("data", []) if s_succ else [])}

            p_succ, pages_res = repo.execute_query(lambda: supabase.table("archon_crawled_pages").select("source_id").execute(), "Fetch crawled pages") # 合法
            indexed_sources = {p["source_id"] for p in (pages_res.get("data", []) if p_succ else [])}

            orphaned_sources = all_sources - indexed_sources
            if orphaned_sources:
                logger.info(f"🧹 Clockwork: Found {len(orphaned_sources)} orphaned RAG sources. Pruning...")
                for sid in orphaned_sources:
                    # Capturing sid in a closure to fix B023
                    def delete_task(s_id=sid):
                        repo.execute_query(lambda: supabase.table("archon_document_versions").delete().eq("document_id", s_id).execute(), "Delete versions") # 合法
                        repo.execute_query(lambda: supabase.table("archon_project_sources").delete().eq("source_id", s_id).execute(), "Delete project sources") # 合法
                        repo.execute_query(lambda: supabase.table("archon_sources").delete().eq("source_id", s_id).execute(), "Delete sources") # 合法
                    delete_task()
                deleted_orphans = len(orphaned_sources)
                logger.info(f"✅ Clockwork: Pruned {deleted_orphans} orphaned sources.")
        except Exception as prune_err:
            logger.warning(f"⚠️ Clockwork: Failed to prune orphaned RAG sources: {prune_err}")

        if any([deleted_leads, deleted_pages, deleted_versions, deleted_sources, deleted_orphans]):
            logger.info(
                f"✅ Clockwork: Cleanup complete. Deleted {deleted_leads} leads, {deleted_pages} pages, "
                f"{deleted_versions} versions, {deleted_sources} sources, {deleted_orphans} orphans."
            )
        else:
            logger.info("✅ Clockwork: Cleanup complete. No expired probe data or RAG orphans found.")
    except Exception as e:
        logger.error(f"💥 Clockwork: System Probe Cleanup Failed: {e}")

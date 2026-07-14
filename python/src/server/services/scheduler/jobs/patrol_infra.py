"""
Infrastructure Patrol Jobs for Scheduler
Handles monitoring of Vercel, Supabase, and Hugging Face infrastructure.
"""

from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)

async def run_infrastructure_audit():
    """Phase 6.1 (now 5.9.2): Patrols the 3 main infrastructures (Vercel, Supabase, HF)."""
    logger.info("🛡️ Clockwork: Starting Infrastructure Patrol...")
    import os

    import httpx

    from src.server.repositories.base_repository import BaseRepository
    from src.server.utils import get_supabase_client

    supabase = get_supabase_client()
    repo = BaseRepository(supabase)

    errors = []

    # 1. Vercel (Frontend Domain)
    frontend_url = os.getenv("FRONTEND_URL", "https://archon-ui-fe.vercel.app")
    if frontend_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(frontend_url)
                if resp.status_code >= 500:
                    errors.append(f"Vercel (Frontend): HTTP {resp.status_code}")
        except Exception as e:
            errors.append(f"Vercel (Frontend): Request failed ({e})")

    # 2. Supabase (pg_stat_activity)
    try:
        res = repo.execute_query(
            lambda: supabase.table("pg_stat_activity").select("pid", count="exact").limit(1).execute(),
            "Check Supabase Connections",
            require_data=False
        )
        if res[0] and res[1] and hasattr(res[1], 'count') and res[1].count is not None:
            if res[1].count > 50:
                errors.append(f"Supabase: Connection pool high ({res[1].count} > 50)")
    except Exception as e:
        errors.append(f"Supabase: pg_stat_activity check failed ({e})")

    # 3. HF Endpoint
    hf_endpoint = os.getenv("HUGGINGFACE_ENDPOINT")
    if hf_endpoint:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # We do a basic GET to see if it's awake/responsive
                resp = await client.get(hf_endpoint)
                if resp.status_code in [503, 504]:
                    errors.append(f"HuggingFace: Endpoint HTTP {resp.status_code}")
        except Exception as e:
            errors.append(f"HuggingFace: Endpoint unreachable ({e})")

    # 4. Tiered Database Pruning (Phase 5.9.3)
    try:
        from datetime import UTC, datetime, timedelta

        from src.server.services.settings_service import SettingsService
        settings = SettingsService(supabase)

        db_size_res = repo.execute_query(
            lambda: supabase.rpc("get_db_size_mb").execute(),
            "Get DB Size",
            require_data=False
        )

        # Handle execution result
        size_data = db_size_res[1] if isinstance(db_size_res, tuple) else None

        if size_data and hasattr(size_data, 'data') and size_data.data is not None:
            db_size_mb = float(size_data.data)

            # Fetch dynamic thresholds
            try:
                max_size_mb = float(str(settings.get_setting("PRUNING_MAX_SIZE_MB", "500.0") or "500.0"))
                l1_pct = float(str(settings.get_setting("PRUNING_L1_PCT", "50.0") or "50.0"))
                l2_pct = float(str(settings.get_setting("PRUNING_L2_PCT", "80.0") or "80.0"))

                l1_logs_days = int(str(settings.get_setting("PRUNING_L1_LOGS_DAYS", "90") or "90"))
                l1_tokens_days = int(str(settings.get_setting("PRUNING_L1_TOKENS_DAYS", "180") or "180"))

                l2_logs_days = int(str(settings.get_setting("PRUNING_L2_LOGS_DAYS", "30") or "30"))
                l2_leads_days = int(str(settings.get_setting("PRUNING_L2_LEADS_DAYS", "90") or "90"))

                l3_logs_days = int(str(settings.get_setting("PRUNING_L3_LOGS_DAYS", "14") or "14"))
                l3_crawled_days = int(str(settings.get_setting("PRUNING_L3_CRAWLED_DAYS", "30") or "30"))
            except ValueError:
                max_size_mb, l1_pct, l2_pct = 500.0, 50.0, 80.0
                l1_logs_days, l1_tokens_days = 90, 180
                l2_logs_days, l2_leads_days = 30, 90
                l3_logs_days, l3_crawled_days = 14, 30

            capacity_pct = (db_size_mb / max_size_mb) * 100

            logger.info(f"Database Capacity: {db_size_mb:.2f}MB ({capacity_pct:.1f}%)")

            # Default Level 1
            threshold_logs = l1_logs_days
            threshold_tokens = l1_tokens_days
            is_level_3 = False

            # Level 2
            if capacity_pct >= l1_pct:
                threshold_logs = l2_logs_days
                dormant_date = (datetime.now(UTC) - timedelta(days=l2_leads_days)).isoformat()
                supabase.table("leads").delete().eq("status", "dormant").lt("created_at", dormant_date).execute()

            # Level 3 (Survival)
            if capacity_pct >= l2_pct:
                threshold_logs = l3_logs_days
                is_level_3 = True

                orphan_res = repo.execute_query(
                    lambda: supabase.rpc("prune_orphan_vectors").execute(),
                    "Prune Orphan Vectors",
                    require_data=False
                )
                orphan_count = orphan_res[1].data if (isinstance(orphan_res, tuple) and orphan_res[1] and hasattr(orphan_res[1], 'data')) else 0
                if orphan_count:
                    logger.warning(f"Survival Pruning: Deleted {orphan_count} orphan vectors.")

                crawled_date = (datetime.now(UTC) - timedelta(days=l3_crawled_days)).isoformat()
                supabase.table("archon_crawled_pages").delete().lt("created_at", crawled_date).execute()

            # Execute common deletions
            log_date = (datetime.now(UTC) - timedelta(days=threshold_logs)).isoformat()
            token_date = (datetime.now(UTC) - timedelta(days=threshold_tokens)).isoformat()

            if is_level_3:
                supabase.table("archon_logs").delete().lt("created_at", log_date).execute()
            else:
                supabase.table("archon_logs").delete().in_("level", ["INFO", "DEBUG"]).lt("created_at", log_date).execute()

            supabase.table("token_usage").delete().lt("created_at", token_date).execute()

            # Recalculate size
            new_size_res = supabase.rpc("get_db_size_mb").execute()
            if new_size_res and hasattr(new_size_res, 'data') and new_size_res.data is not None:
                freed_mb = db_size_mb - float(new_size_res.data)
                if freed_mb > 0.01:
                    logger.info(f"Tiered Pruning completed. Freed {freed_mb:.2f}MB.")
    except Exception as e:
        logger.error(f"Tiered Database Pruning failed: {e}")

    # Log results
    if errors:
        logger.error(f"❌ Clockwork: Infrastructure Patrol found issues: {', '.join(errors)}")
        repo.execute_query(
            lambda: supabase.table("archon_logs").insert({
                "source": "infra-patrol",
                "level": "ERROR",
                "message": "Infrastructure Patrol detected anomalies",
                "details": {"errors": errors}
            }).execute(),
            "Log infra errors"
        )
    else:
        logger.info("✅ Clockwork: Infrastructure Patrol passed. All systems nominal.")

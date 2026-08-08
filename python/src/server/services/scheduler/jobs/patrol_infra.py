"""
Infrastructure Patrol Jobs for Scheduler
Handles monitoring of Vercel, Supabase, and Hugging Face infrastructure.
"""

from src.server.config.logfire_config import get_logger
from src.server.schemas.settings import NetworkConfig, PruningConfig

logger = get_logger(__name__)


async def run_infrastructure_audit() -> None:
    """Phase 6.1 (now 5.9.2): Patrols the 3 main infrastructures (Vercel, Supabase, HF)."""
    logger.info("🛡️ Clockwork: Starting Infrastructure Patrol...")

    import httpx

    from src.server.repositories.base_repository import BaseRepository
    from src.server.utils import get_supabase_client

    supabase = get_supabase_client()
    repo = BaseRepository(supabase)

    errors = []

    # 1. Vercel (Frontend Domain)
    frontend_url = NetworkConfig().frontend_url
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
            supabase.table("pg_stat_activity").select("pid", count="exact").limit(1), # 合法
            "Check Supabase Connections",
            require_data=False
        )
        if res[0] and res[1] and hasattr(res[1], 'count') and res[1].count is not None:
            if res[1].count > 50:
                errors.append(f"Supabase: Connection pool high ({res[1].count} > 50)")
    except Exception as e:
        errors.append(f"Supabase: pg_stat_activity check failed ({e})")

    # 3. HF Endpoint
    from src.server.services.settings_service import SettingsService
    hf_endpoint = SettingsService(supabase).get_setting("HUGGINGFACE_ENDPOINT")
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
            supabase.rpc("get_db_size_mb"),
            "Get DB Size",
            require_data=False
        )

        # Handle execution result
        size_data = db_size_res[1] if isinstance(db_size_res, tuple) else None

        if size_data and hasattr(size_data, 'data') and size_data.data is not None:
            db_size_mb = float(size_data.data)

            # Fetch dynamic thresholds using Pydantic SSOT
            raw_settings = settings.get_all_settings()
            try:
                config = PruningConfig.model_validate(raw_settings)
            except Exception as e:
                logger.warning(f"Failed to parse PruningConfig, falling back to defaults: {e}")
                config = PruningConfig()

            capacity_pct = (db_size_mb / config.max_size_mb) * 100

            logger.info(f"Database Capacity: {db_size_mb:.2f}MB ({capacity_pct:.1f}%)")

            # Default Level 1
            threshold_logs = config.l1_logs_days
            threshold_tokens = config.l1_tokens_days
            is_level_3 = False

            # Level 2
            if capacity_pct >= config.l1_pct:
                threshold_logs = config.l2_logs_days
                threshold_tokens = config.l2_tokens_days
                dormant_date = (datetime.now(UTC) - timedelta(days=config.l2_leads_days)).isoformat()
                repo.execute_query(
                    supabase.table("leads").delete().eq("status", "dormant").lt("created_at", dormant_date), # 合法
                    "Prune dormant leads",
                    require_data=False
                )

            # Level 3 (Survival)
            if capacity_pct >= config.l2_pct:
                threshold_logs = config.l3_logs_days
                threshold_tokens = config.l3_tokens_days
                is_level_3 = True

                orphan_res = repo.execute_query(
                    supabase.rpc("prune_orphan_vectors"),
                    "Prune Orphan Vectors",
                    require_data=False
                )
                orphan_count = orphan_res[1].data if (isinstance(orphan_res, tuple) and orphan_res[1] and hasattr(orphan_res[1], 'data')) else 0
                if orphan_count:
                    logger.warning(f"Survival Pruning: Deleted {orphan_count} orphan vectors.")

                crawled_date = (datetime.now(UTC) - timedelta(days=config.l3_crawled_days)).isoformat()
                repo.execute_query(
                    supabase.table("archon_crawled_pages").delete().lt("created_at", crawled_date), # 合法
                    "Prune crawled pages",
                    require_data=False
                )

            # Execute common deletions
            log_date = (datetime.now(UTC) - timedelta(days=threshold_logs)).isoformat()
            token_date = (datetime.now(UTC) - timedelta(days=threshold_tokens)).isoformat()

            if is_level_3:
                repo.execute_query(
                    supabase.table("archon_logs").delete().lt("created_at", log_date), # 合法
                    "Prune all logs (Level 3)",
                    require_data=False
                )
            else:
                repo.execute_query(
                    supabase.table("archon_logs").delete().in_("level", ["INFO", "DEBUG"]).lt("created_at", log_date), # 合法
                    "Prune info/debug logs",
                    require_data=False
                )

            repo.execute_query(
                supabase.table("token_usage").delete().lt("created_at", token_date), # 合法
                "Prune token usage",
                require_data=False
            )

            # Recalculate size
            new_size_succ, new_size_res = repo.execute_query(
                supabase.rpc("get_db_size_mb"),
                "Get new DB Size",
                require_data=False
            )
            if new_size_succ and new_size_res and hasattr(new_size_res, 'data') and new_size_res.data is not None:
                freed_mb = db_size_mb - float(new_size_res.data)
                if freed_mb > 0.01:
                    logger.info(f"Tiered Pruning completed. Freed {freed_mb:.2f}MB.")
    except Exception as e:
        logger.error(f"Tiered Database Pruning failed: {e}")

    # Log results
    if errors:
        logger.error(f"❌ Clockwork: Infrastructure Patrol found issues: {', '.join(errors)}")
        repo.execute_query(
            supabase.table("archon_logs").insert({ # 合法
                "source": "infra-patrol",
                "level": "ERROR",
                "message": "Infrastructure Patrol detected anomalies",
                "details": {"errors": errors}
            }),
            "Log infra errors"
        )
    else:
        logger.info("✅ Clockwork: Infrastructure Patrol passed. All systems nominal.")

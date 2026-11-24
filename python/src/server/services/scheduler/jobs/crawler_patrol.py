"""
Whitelist Crawler Patrol Job for Scheduler (Phase 5.13).
Periodically crawls active archon_crawler_targets whose update_frequency is not 'manual'.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from src.server.config.logfire_config import get_logger
from src.server.repositories.base_repository import BaseRepository
from src.server.utils import get_supabase_client

logger = get_logger(__name__)

FREQUENCY_DAYS: dict[str, int] = {
    "daily": 1,
    "weekly": 7,
    "bi-weekly": 14,
    "monthly": 30,
}


def _is_target_due(target: dict[str, Any], now: datetime) -> bool:
    """Return True if the target is active, non-manual, and due for a scheduled crawl."""
    if not target.get("is_active"):
        return False

    freq = str(target.get("update_frequency") or "manual").strip().lower()
    interval_days = FREQUENCY_DAYS.get(freq)
    if interval_days is None:
        return False

    last_crawled_raw = target.get("last_crawled_at")
    if not last_crawled_raw:
        return True

    try:
        last_crawled_dt = datetime.fromisoformat(str(last_crawled_raw).replace("Z", "+00:00"))
        if last_crawled_dt.tzinfo is None:
            last_crawled_dt = last_crawled_dt.replace(tzinfo=UTC)
        return (now - last_crawled_dt) >= timedelta(days=interval_days)
    except ValueError:
        logger.warning(f"Invalid last_crawled_at '{last_crawled_raw}' for target {target.get('id')}; treating as due.")
        return True


async def run_whitelist_crawler_patrol() -> int:
    """Crawl due active targets from archon_crawler_targets and update last_crawled_at."""
    from src.server.services.crawling.crawling_service import CrawlingService

    logger.info("🕷️ Clockwork: Checking scheduled whitelist crawler targets...")
    supabase = get_supabase_client()
    repo = BaseRepository(supabase)

    success, res = repo.execute_query(
        supabase.table("archon_crawler_targets")
        .select("id, target_url, max_depth, is_active, update_frequency, last_crawled_at")
        .eq("is_active", True),
        "Fetch active crawler targets",
    )
    if not success or not isinstance(res, dict):
        logger.error("Failed to fetch archon_crawler_targets for scheduled patrol.")
        return 0

    targets = res.get("data") or []
    now = datetime.now(UTC)
    crawled_count = 0
    crawler = CrawlingService(supabase_client=supabase)

    for target in targets:
        if not isinstance(target, dict) or not _is_target_due(target, now):
            continue

        target_id = target.get("id")
        target_url = target.get("target_url")
        if not target_url:
            continue

        try:
            logger.info(f"🕷️ Whitelist Patrol: Crawling due target '{target_url}' (freq={target.get('update_frequency')})")
            await crawler.orchestrate_crawl(
                {
                    "url": target_url,
                    "max_depth": target.get("max_depth") or 2,
                    "user_role": "system_admin",
                }
            )
            repo.execute_query(
                supabase.table("archon_crawler_targets")
                .update({"last_crawled_at": now.isoformat()})
                .eq("id", target_id),
                f"Update last_crawled_at for target {target_id}",
            )
            crawled_count += 1
        except Exception as e:
            logger.error(f"💥 Whitelist Patrol failed for '{target_url}': {e}", exc_info=True)

    logger.info(f"✅ Clockwork: Whitelist crawler patrol finished ({crawled_count} targets crawled).")
    return crawled_count

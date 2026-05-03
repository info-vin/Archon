import logging
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

class KnowledgeMetrics:
    """Handles knowledge base growth and ROI tracking."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def get_knowledge_roi(self) -> dict[str, Any]:
        """Knowledge Graph ROI calculation (Phase 4.6.15)."""
        now = datetime.now(UTC)
        cutoff = (now - timedelta(days=60)).isoformat()
        try:
            sources_res = self.supabase.table("archon_sources").select("source_id, source_url, created_at").gt("created_at", cutoff).execute()
            pages_res = self.supabase.table("archon_crawled_pages").select("source_id, created_at").gt("created_at", cutoff).execute()

            sources = sources_res.data or []
            pages = pages_res.data or []

            parsed_sources = []
            for s in sources:
                if raw := s.get("created_at"):
                    try:
                        parsed_sources.append((s, datetime.fromisoformat(str(raw).replace("Z", "+00:00"))))
                    except Exception:
                        pass

            parsed_pages = []
            for p in pages:
                if raw := p.get("created_at"):
                    try:
                        parsed_pages.append((p, datetime.fromisoformat(str(raw).replace("Z", "+00:00"))))
                    except Exception:
                        pass

            trend_data = []
            for i in range(60, 0, -14):
                w_start, w_end = now - timedelta(days=i), now - timedelta(days=i - 14)
                w_sources = [s for s, dt in parsed_sources if w_start <= dt < w_end]
                w_pages = [p for p, dt in parsed_pages if w_start <= dt < w_end]
                trend_data.append({
                    "date": w_start.strftime("%m-%d"),
                    "conversion": round((len(w_pages) / len(w_sources)) * 100, 1) if w_sources else 0.0,
                    "scanned": len(w_sources),
                    "saved": len(w_pages),
                })

            return {
                "overall_conversion": round((len(pages) / len(sources)) * 100, 1) if sources else 0.0,
                "trend": trend_data,
                "timestamp": now.isoformat(),
            }
        except Exception as e:
            logger.error(f"KnowledgeMetrics: Knowledge ROI failed: {e}")
            return {"overall_conversion": 0.0, "trend": []}

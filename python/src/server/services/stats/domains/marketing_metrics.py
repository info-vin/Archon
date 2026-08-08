import logging
from datetime import UTC, datetime
from typing import Any

from ....repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)




class MarketingMetrics(BaseRepository):
    """Handles deep lead analysis and marketing ROI."""

    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client)
        self.supabase: Any = self.supabase_client

    async def get_marketing_intelligence(self, user_id: str | None = None) -> dict[str, Any]:
        """Marketing 2.0: Deep Lead Analysis & ROI (Phase 4.6.42)."""
        try:
            query = self.supabase.table("leads").select("*") # 合法
            if user_id:
                query = query.or_(f"assigned_sales_id.eq.{user_id},assigned_sales_id.is.null")
            success, res = self.execute_query(query, "Get marketing intelligence leads")
            leads = res.get("data", []) if success else []

            # 1. Conversion Funnel (Physical Data)
            funnel = {"new": 0, "contacted": 0, "shortlisted": 0, "converted": 0, "archived": 0}
            for lead in leads:
                s = lead.get("status", "new")
                if s in funnel:
                    funnel[s] += 1

            # 2. Industry/Job Distribution (Keyword Proxy)
            categories = {
                "AI/ML": ["AI", "Machine Learning", "ML", "Deep Learning"],
                "Data/Analytics": ["Data", "Analyst", "Statistics"], # 合法
                "Engineering": ["Engineer", "Developer", "Backend", "Frontend", "Python"], # 合法
                "Marketing/Sales": ["Marketing", "Sales", "Business", "Brand"], # 合法
                "Management": ["Manager", "Director", "VP", "Lead"], # 合法
            }

            distribution: dict[str, int] = dict.fromkeys(categories, 0)
            distribution["Other"] = 0

            # PERFORMANCE: Precalculate uppercase keywords outside the loop to avoid redundant allocations
            categories_upper = {cat: [k.upper() for k in keywords] for cat, keywords in categories.items()}

            for lead in leads:
                title = str(lead.get("job_title") or "").upper()
                found = False
                for cat, keywords_upper in categories_upper.items():
                    if any(k in title for k in keywords_upper):
                        distribution[cat] += 1
                        found = True
                        break
                if not found:
                    distribution["Other"] += 1

            # 3. ROI & Velocity
            # Calculate average conversion velocity (GAP-034)
            velocity_sum = 0.0
            converted_count = 0
            for lead in leads:
                if lead.get("status") == "converted" and lead.get("updated_at") and lead.get("created_at"):
                    start = datetime.fromisoformat(lead["created_at"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(lead["updated_at"].replace("Z", "+00:00"))
                    velocity_sum += (end - start).total_seconds() / 3600
                    converted_count += 1

            avg_velocity = round(velocity_sum / converted_count, 1) if converted_count > 0 else 0.0

            return {
                "total_leads": len(leads),
                "funnel": funnel,
                "distribution": distribution,
                "metrics": {
                    "avg_conversion_hours": avg_velocity,
                    "high_value_percentage": round(
                        (distribution["AI/ML"] + distribution["Management"]) / len(leads) * 100, 1
                    )
                    if leads
                    else 0.0,
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }
        except Exception as e:
            logger.error(f"MarketingMetrics: Marketing intelligence failed: {e}")
            return {"error": str(e)}

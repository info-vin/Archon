import logging
import os
from typing import Any

import aiofiles

from ..librarian_service import LibrarianService
from ..shared_constants import StatusEnum

logger = logging.getLogger(__name__)


class AnalyticsHandler:
    """
    Handles Marketing Stats, Trends, Knowledge Seeding, and Sentinel Triggers.
    Consolidates background and data-heavy logic for Phase 4.6.47.
    """

    def __init__(self, supabase_client: Any) -> None:
        self.supabase_client = supabase_client

    async def get_marketing_stats(self) -> dict:
        try:
            leads_count = self.supabase_client.table("leads").select("id", count="exact").execute().count or 0
            blogs_count = self.supabase_client.table("blog_posts").select("id", count="exact").execute().count or 0
            converted_leads = (
                self.supabase_client.table("leads")
                .select("id", count="exact")
                .eq("status", "converted")
                .execute()
                .count
                or 0
            )

            return {
                "total_leads": leads_count,
                "total_blog_posts": blogs_count,
                "conversion_rate": round((converted_leads / leads_count * 100), 2) if leads_count > 0 else 0,
                "active_campaigns": blogs_count,
                "last_updated": "2026-03-20T10:00:00Z",
            }
        except Exception as e:
            logger.error(f"AnalyticsHandler: Failed to fetch stats: {e}")
            return {"error": str(e)}

    async def get_marketing_trends(self) -> dict:
        try:
            res_t = (
                self.supabase_client.table("marketing_trends")
                .select("*")
                .eq("trend_type", "keyword_growth")
                .order("report_date", desc=True)
                .limit(1)
                .execute()
            )
            res_s = (
                self.supabase_client.table("marketing_trends")
                .select("*")
                .eq("trend_type", "sankey_flow")
                .order("report_date", desc=True)
                .limit(1)
                .execute()
            )
            return {
                "keyword_growth": res_t.data[0]["data"] if res_t.data else [],
                "sankey_flow": res_s.data[0]["data"] if res_s.data else {},
            }
        except Exception as e:
            logger.error(f"AnalyticsHandler: Failed to fetch trends: {e}")
            return {"keyword_growth": [], "sankey_flow": {}}

    async def run_sentinel(self) -> dict:
        from ..scheduler_service import scheduler_service

        await scheduler_service.run_business_sentinel()
        return {"status": "triggered", "message": "Sentinel scan started in background."}

    async def seed_knowledge(self) -> dict:
        target_dir = "/app/frontend_public/aus/156_resource"
        if not os.path.exists(target_dir):
            target_dir = "../enduser-ui-fe/public/aus/156_resource"

        if not os.path.exists(target_dir):
            return {"error": f"Knowledge resource directory not found at {target_dir}."}

        librarian = LibrarianService()
        success_count = 0
        total_count = 0
        errors = []

        try:
            for root, _, files in os.walk(target_dir):
                for file in files:
                    if file.startswith(".") or file == "DS_Store":
                        continue
                    if not (file.endswith(".md") or file.endswith(".txt")):
                        continue

                    total_count += 1
                    file_path = os.path.join(root, file)
                    try:
                        async with aiofiles.open(file_path, encoding="utf-8") as f:
                            content = await f.read()
                        if not content.strip():
                            continue
                        await librarian.archive_file(
                            file_name=file, content=content, file_path=file_path, knowledge_type="technical"
                        )
                        success_count += 1
                    except Exception as e:
                        errors.append(f"{file}: {str(e)}")

            return {
                "status": "completed",
                "scanned_dir": target_dir,
                "total_files": total_count,
                "indexed_count": success_count,
                "errors": errors[:5],
            }
        except Exception as e:
            return {"error": f"Seeding failed: {str(e)}"}

    async def get_combined_sources(self, user_id: str) -> list[dict]:
        leads = (
            self.supabase_client.table("leads")
            .select("*")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
            .data
            or []
        )
        tasks = (
            self.supabase_client.table("archon_tasks")
            .select("*")
            .eq("assignee_id", user_id)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
            .data
            or []
        )
        blogs = (
            self.supabase_client.table("blog_posts")
            .select("*")
            .in_("status", [StatusEnum.DRAFT, StatusEnum.CHANGES_REQUESTED])
            .order("created_at", desc=True)
            .limit(10)
            .execute()
            .data
            or []
        )

        sources = []
        for lead_entry in leads:
            sources.append(
                {
                    "id": lead_entry["id"],
                    "type": "lead",
                    "title": lead_entry["company_name"],
                    "score": lead_entry.get("enrichment_score", 0),
                    "summary": (lead_entry.get("identified_need") or "")[:100],
                    "date": lead_entry["created_at"],
                }
            )
        for task_entry in tasks:
            sources.append(
                {
                    "id": task_entry["id"],
                    "type": "task",
                    "title": task_entry["title"],
                    "score": 100,
                    "summary": task_entry.get("description", "")[:100],
                    "date": task_entry["created_at"],
                }
            )
        for blog_entry in blogs:
            sources.append(
                {
                    "id": blog_entry["id"],
                    "type": "blog",
                    "title": blog_entry["title"],
                    "score": blog_entry.get("ai_score", 0),
                    "summary": blog_entry.get("excerpt", ""),
                    "date": blog_entry["created_at"],
                    "status": blog_entry["status"],
                }
            )
        return sorted(sources, key=lambda x: x["date"], reverse=True)

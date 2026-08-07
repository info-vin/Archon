import logging
from typing import Any

from ...repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)




class LeadHandler(BaseRepository):
    """
    Handles all Leads CRUD and scoring logic for MarketingService.
    Physically decoupled for Phase 4.6.47.
    """

    def __init__(self, supabase_client: Any) -> None:
        super().__init__(supabase_client)

    async def list_leads(self, user_id: str | None = None, role: str | None = None) -> list[dict]:
        q = self.supabase_client.table("leads").select("*")  # 合法
        if role == "sales" and user_id:
            q = q.or_(f"assigned_sales_id.eq.{user_id},assigned_sales_id.is.null")
        query = q.order("created_at", desc=True)

        success, res = self.execute_query(query, "Failed to fetch leads")
        return res.data if success and hasattr(res, "data") and res.data is not None else []

    async def create_lead(self, lead_data: dict, creator_id: str | None = None) -> tuple[bool, dict]:
        if "created_from_user_id" in lead_data:
            del lead_data["created_from_user_id"]

        if not lead_data.get("enrichment_score") or lead_data.get("enrichment_score") == 0:
            lead_data["enrichment_score"] = await self.calculate_lead_score(lead_data.get("job_title"))

        source_url = lead_data.get("source_job_url")
        if source_url:


            _, existing = self.execute_query(self.supabase_client.table("leads").select("id").eq("source_job_url", source_url), "Check existing lead")  # 合法
            if hasattr(existing, "data") and existing.data:
                if lead_data.get("pitch_content"):
                    self.execute_query(
                        self.supabase_client.table("leads").update({"pitch_content": lead_data["pitch_content"]}).eq("id", existing.data[0]["id"]),  # 合法
                        "Update pitch content"
                    )
                return True, {"lead": existing.data[0]}


        success, res = self.execute_query(self.supabase_client.table("leads").insert(lead_data), "Failed to create lead")  # 合法
        if success and hasattr(res, "data") and res.data:
            return True, {"lead": res.data[0]}
        return False, res

    async def update_lead(self, lead_id: str, update_data: dict) -> tuple[bool, dict]:

        success, res = self.execute_query(self.supabase_client.table("leads").update(update_data).eq("id", lead_id), f"Failed to update lead {lead_id}")  # 合法
        if success and hasattr(res, "data") and res.data:
            lead_data = res.data[0]
            if lead_data.get("status") == "LOST":
                try:
                    from ..librarian_service import LibrarianService

                    librarian = LibrarianService()
                    # The lead data will contain company_name and job_title. We extract lost_reason.
                    reason = update_data.get("lost_reason", "No reason provided")
                    company = lead_data.get("company_name", "Unknown Company")
                    job = lead_data.get("job_title", "Unknown Job")
                    import asyncio

                    # Run archiving as a background task to prevent blocking the UI
                    asyncio.create_task(
                        librarian.archive_failure_case(
                            content=f"Lead marked as LOST. Need: {lead_data.get('identified_need')}",
                            reason=reason,
                            company=company,
                            job_title=job,
                            metadata={"lead_id": lead_id},
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to archive failure case for lead {lead_id}: {e}")
            return True, {"lead": lead_data}
        return False, res

    async def promote_to_vendor(
        self, lead_id: str, vendor_name: str, email: str | None, notes: str | None, owner_id: str
    ) -> tuple[bool, dict]:
        try:
            vendor_data = {
                "name": vendor_name,
                "contact_email": email,
                "description": notes or "Promoted",
                "status": "active",
                "owner_id": owner_id,
            }
            success, vendor_res = self.execute_query(self.supabase_client.table("vendors").insert(vendor_data), "Insert vendor")  # 合法
            if not success or not vendor_res.get("data"):
                return False, {"error": "Failed to create vendor"}

            new_vendor_id = vendor_res["data"][0]["id"]
            self.execute_query(self.supabase_client.table("leads").update({"status": "converted"}).eq("id", lead_id), "Update lead status")  # 合法
            self.execute_query(self.supabase_client.table("visit_logs").update({"customer_id": new_vendor_id}).eq("lead_id", lead_id), "Update visit logs")  # 合法
            return True, {"vendor": vendor_res["data"][0]}
        except Exception as e:
            return False, {"error": str(e)}

    async def calculate_lead_score(self, job_title: str | None) -> int:
        try:
            from ..settings_service import SettingsService

            settings = SettingsService(self.supabase_client)
            from ...schemas.settings import LeadScoringConfig
            try:
                config = LeadScoringConfig.model_validate(settings.get_all_settings())
            except Exception as e:
                logger.warning(f"Failed to parse LeadScoringConfig, using defaults: {e}")
                config = LeadScoringConfig()

            w_strat = config.score_strategic
            w_tech = config.score_technical
            w_ops = config.score_operational
            w_base = config.score_base

            title = str(job_title or "").upper()
            if any(kw in title for kw in ["DIRECTOR", "VP", "HEAD", "CHIEF", "ARCHITECT", "FOUNDER"]): # 合法
                return w_strat
            if any(kw in title for kw in ["AI", "ML", "MACHINE LEARNING", "DATA", "PYTHON", "ENGINEER"]):
                return w_tech
            if any(kw in title for kw in ["MANAGER", "LEAD", "SENIOR", "TEAM LEAD"]):
                return w_ops
            return w_base
        except Exception as e:
            logger.warning(f"Lead Scoring Failed: {e}. Falling back to 40.")
            return 40

    async def reset_leads(self) -> bool:
        try:
            self.execute_query(self.supabase_client.table("leads").delete().neq("id", "00000000-0000-0000-0000-000000000000"), "Reset leads")  # 合法
            return True
        except Exception as e:
            logger.error(f"Failed to reset leads: {e}")
            return False

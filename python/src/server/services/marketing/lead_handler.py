import logging
from typing import Any

logger = logging.getLogger(__name__)

class LeadHandler:
    """
    Handles all Leads CRUD and scoring logic for MarketingService.
    Physically decoupled for Phase 4.6.47.
    """

    def __init__(self, supabase_client: Any):
        self.supabase_client = supabase_client

    def execute_query(self, query_func, error_msg: str) -> tuple[bool, Any]:
        """Helper to maintain parity with BaseRepository-like execution."""
        try:
            res = query_func()
            return True, res
        except Exception as e:
            logger.error(f"{error_msg}: {e}")
            return False, {"error": str(e)}

    async def list_leads(self, user_id: str | None = None, role: str | None = None) -> list[dict]:
        def _query():
            q = self.supabase_client.table("leads").select("*")
            if role == "sales" and user_id:
                q = q.or_(f"assigned_sales_id.eq.{user_id},assigned_sales_id.is.null")
            return q.order("created_at", desc=True).execute()

        success, res = self.execute_query(_query, "Failed to fetch leads")
        return res.data if success and hasattr(res, "data") and res.data is not None else []

    async def create_lead(self, lead_data: dict, creator_id: str | None = None) -> tuple[bool, dict]:
        lead_data["created_from_user_id"] = creator_id
        if not lead_data.get("enrichment_score") or lead_data.get("enrichment_score") == 0:
            lead_data["enrichment_score"] = await self.calculate_lead_score(lead_data.get("job_title"))

        source_url = lead_data.get("source_job_url")
        if source_url:
            def _check_existing():
                return self.supabase_client.table("leads").select("id").eq("source_job_url", source_url).execute()
            _, existing = self.execute_query(_check_existing, "Check existing lead")
            if hasattr(existing, "data") and existing.data:
                if lead_data.get("pitch_content"):
                    self.supabase_client.table("leads").update({"pitch_content": lead_data["pitch_content"]}).eq(
                        "id", existing.data[0]["id"]
                    ).execute()
                return True, {"lead": existing.data[0]}

        def _insert():
            return self.supabase_client.table("leads").insert(lead_data).execute()

        success, res = self.execute_query(_insert, "Failed to create lead")
        if success and hasattr(res, "data") and res.data:
            return True, {"lead": res.data[0]}
        return False, res

    async def update_lead(self, lead_id: str, update_data: dict) -> tuple[bool, dict]:
        def _query():
            return self.supabase_client.table("leads").update(update_data).eq("id", lead_id).execute()
        success, res = self.execute_query(_query, f"Failed to update lead {lead_id}")
        if success and hasattr(res, "data") and res.data:
            return True, {"lead": res.data[0]}
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
            vendor_res = self.supabase_client.table("vendors").insert(vendor_data).execute()
            new_vendor_id = vendor_res.data[0]["id"]
            self.supabase_client.table("leads").update({"status": "converted"}).eq("id", lead_id).execute()
            self.supabase_client.table("visit_logs").update({"customer_id": new_vendor_id}).eq(
                "lead_id", lead_id
            ).execute()
            return True, {"vendor": vendor_res.data[0]}
        except Exception as e:
            return False, {"error": str(e)}

    async def calculate_lead_score(self, job_title: str | None) -> int:
        try:
            from ..settings_service import SettingsService
            settings = SettingsService(self.supabase_client)
            w_strat = int(settings.get_setting("SCORE_STRATEGIC") or "95")
            w_tech = int(settings.get_setting("SCORE_TECHNICAL") or "85")
            w_ops = int(settings.get_setting("SCORE_OPERATIONAL") or "70")
            w_base = int(settings.get_setting("SCORE_BASE") or "40")

            title = str(job_title or "").upper()
            if any(kw in title for kw in ["DIRECTOR", "VP", "HEAD", "CHIEF", "ARCHITECT", "FOUNDER"]):
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
            self.supabase_client.table("leads").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            return True
        except Exception as e:
            logger.error(f"Failed to reset leads: {e}")
            return False

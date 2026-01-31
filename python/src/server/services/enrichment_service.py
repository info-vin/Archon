import asyncio
from datetime import datetime, timedelta

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

class EnrichmentService:
    """
    Service to handle the enrichment loop for leads.
    1. Tries to fetch more data from 104 (via JobBoardService) or Google Search (Mocked).
    2. Prunes stale leads that haven't been converted or enriched in time.
    """

    @staticmethod
    async def enrich_lead(lead_id: str):
        """
        Attempts to enrich a single lead with external data.
        """
        supabase = get_supabase_client()
        try:
            # Fetch lead
            res = supabase.table("leads").select("*").eq("id", lead_id).single().execute()
            if not res.data:
                logger.warning(f"Enrichment: Lead not found | id={lead_id}")
                return False

            lead = res.data
            if lead.get("enrichment_status") == "success":
                return True

            logger.info(f"Enrichment: Starting | id={lead_id} | company={lead.get('company_name')}")

            # Check Toggle for Real vs Mock
            from ..services.credential_service import credential_service
            # We reuse 'rag_strategy' category as per migration
            enable_real = await credential_service.get_credential("ENABLE_REAL_ENRICHMENT")
            is_real_mode = str(enable_real).lower() == "true"

            if is_real_mode:
                logger.info(f"Enrichment: Running in REAL mode (Simulated Real API Call) | id={lead_id}")
                # Real Implementation Hook:
                # 1. Get JobBoard/Google API Key
                # 2. Call Crawler
                # 3. Parse results
                # For Phase 4.6, we simulate a 'Real' call taking longer or hitting a different endpoint
                await asyncio.sleep(3.0)
            else:
                logger.info(f"Enrichment: Running in MOCK mode | id={lead_id}")
                await asyncio.sleep(1.5)

            # logic: If successful, update status and score
            # Real implementation would call scraping tools here.

            enrichment_data = {
                "enrichment_status": "success",
                "enrichment_score": 85, # Mock score
                "data_last_verified_at": datetime.now().isoformat(),
            }

            supabase.table("leads").update(enrichment_data).eq("id", lead_id).execute()
            logger.info(f"Enrichment: Success | id={lead_id}")
            return True

        except Exception as e:
            logger.error(f"Enrichment: Failed | id={lead_id} | error={str(e)}")
            supabase.table("leads").update({"enrichment_status": "failed"}).eq("id", lead_id).execute()
            return False

    @staticmethod
    async def prune_stale_leads() -> int:
        """
        Auto-archives leads that are > 3 days old and have low enrichment scores or remain new.
        Returns count of pruned leads.
        """
        supabase = get_supabase_client()
        try:
            # Find leads > 3 days old
            three_days_ago = (datetime.now() - timedelta(days=3)).isoformat()

            # Fetch potential stale leads
            # Condition: created_at < 3 days ago AND status != archived AND status != converted
            res = supabase.table("leads").select("*")\
                .lt("created_at", three_days_ago)\
                .neq("status", "archived")\
                .neq("status", "converted")\
                .execute()

            if not res.data:
                return 0

            pruned_count = 0
            for lead in res.data:
                # Criteria: failed enrichment or score < 50
                score = lead.get("enrichment_score") or 0
                status = lead.get("enrichment_status")

                if status == "failed" or score < 50:
                    logger.info(f"Pruning stale lead | id={lead['id']} | reason=stale_low_quality")
                    supabase.table("leads").update({
                        "status": "archived",
                        "auto_archived_reason": "stale_low_quality"
                    }).eq("id", lead["id"]).execute()
                    pruned_count += 1

            return pruned_count

        except Exception as e:
            logger.error(f"Pruning failed | error={str(e)}")
            return 0

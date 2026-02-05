import asyncio
import os  # Added import
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

            # Generate Mock Enriched Data
            mock_tax_id = "12345678"
            mock_email = f"contact@{lead.get('company_name', 'company').lower().replace(' ', '')}.com"
            mock_news = "Recent news indicates expansion into AI sector with $10M Series B funding."

            # Append to identified_need for visibility
            current_need = lead.get("identified_need") or ""
            enriched_summary = f"{current_need}\n\n[Auto-Enriched Data]\nTax ID: {mock_tax_id}\nEmail: {mock_email}\nNews: {mock_news}"

            # Implement GAP-015: Dynamic Scoring via SettingsService
            from ..services.settings_service import SettingsService
            settings_service = SettingsService(supabase)

            # Fetch rules (with defaults)
            score_vital = int(settings_service.get_setting("SCORING_VITAL_CONTACT", "20") or "20")
            score_funding = int(settings_service.get_setting("SCORING_NEWS_FUNDING", "30") or "30")
            score_job = int(settings_service.get_setting("SCORING_HAS_JOB_URL", "15") or "15")

            base_score = 20 # Baseline for existing
            if mock_email:
                base_score += score_vital
            if "funding" in mock_news.lower():
                base_score += score_funding
            if lead.get("source_job_url"):
                base_score += score_job

            enrichment_data = {
                "enrichment_status": "success",
                "enrichment_score": base_score,
                "data_last_verified_at": datetime.now().isoformat(),
                "identified_need": enriched_summary,
                "contact_email": mock_email # Try saving to column if exists (based on API usage)
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
        Auto-archives leads that are > 3 days old and have low enrichment scores.
        Uses a single SQL-like batch update for performance.
        Returns count of pruned leads.
        """
        supabase = get_supabase_client()
        try:
            # 1. Determine threshold
            threshold_minutes = os.getenv("PRUNING_THRESHOLD_MINUTES")
            if threshold_minutes:
                try:
                    delta = timedelta(minutes=int(threshold_minutes))
                    logger.info(f"Pruning: Using configurable threshold: {threshold_minutes} minutes")
                except ValueError:
                    delta = timedelta(days=3)
            else:
                delta = timedelta(days=3)

            cutoff_time = (datetime.now() - delta).isoformat()

            # 2. Execute Batch Update (Equivalent to SQL UPDATE WHERE ...)
            # Criteria: Created < cutoff AND Score < 40 (GAP-011) AND Not already processed
            logger.info(f"Pruning: Executing batch archive for leads created before {cutoff_time} with score < 40")

            res = supabase.table("leads").update({
                "status": "archived",
                "auto_archived_reason": "stale_low_quality"
            })\
            .lt("created_at", cutoff_time)\
            .lt("enrichment_score", 40)\
            .neq("status", "archived")\
            .neq("status", "converted")\
            .execute()

            pruned_count = len(res.data) if res.data else 0

            if pruned_count > 0:
                logger.info(f"Pruning: Successfully archived {pruned_count} stale leads.")

            return pruned_count

        except Exception as e:
            logger.error(f"Pruning failed | error={str(e)}")
            return 0

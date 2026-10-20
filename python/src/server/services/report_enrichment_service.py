"""
Report Enrichment Service
Handles optional high-value additions to reports like Nexus Oracle insights and TTS Podcast generation.
"""

import asyncio

from src.server.config.logfire_config import get_logger
from src.server.schemas.settings import TTSConfig

logger = get_logger(__name__)


class ReportEnrichmentService:

    @staticmethod
    async def inject_nexus_oracle_insights(context_md: str) -> str:
        """Invokes NexusOracleAgent and appends its insights to the context."""
        logger.info("🔮 ReportEnrichmentService: Invoking NexusOracleAgent for high-level insights...")
        try:
            from src.server.services.prompt_service import prompt_service
            from src.server.services.shared_constants import PromptNameEnum

            system_prompt = prompt_service.get_prompt(PromptNameEnum.NEXUS_ORACLE_AGENT_PROMPT.value)

            from src.agents.nexus_oracle_agent import NexusDependencies, NexusOracleAgent
            oracle = NexusOracleAgent()
            # Fail fast with 25s timeout to prevent hanging on Google Free Tier 429 rate limit backoffs
            oracle_res = await asyncio.wait_for(
                oracle.run(system_prompt, deps=NexusDependencies()),
                timeout=25.0
            )
            state_data = oracle_res
            oracle_md = (
                f"### 🔮 Nexus Oracle Insight\n"
                f"- **System Health**: {state_data.health_score} ({state_data.system_status})\n"
                f"- **Main Bottleneck**: {state_data.main_bottleneck}\n"
                f"- **Monthly Forecast**: {state_data.long_term_trends.monthly_budget_forecast}\n"
            )
            if state_data.recommended_actions:
                oracle_md += "- **Recommended Actions**:\n"
                for act in state_data.recommended_actions:
                    oracle_md += f"  - [{act.risk_level}] {act.action_id}: {act.reason}\n"
            context_md += f"\n\n{oracle_md}"
            logger.info("✅ ReportEnrichmentService: Nexus Oracle insights injected.")
        except Exception as e:
            logger.warning(f"⚠️ ReportEnrichmentService: Skipped Nexus Oracle insights due to rate-limit/timeout: {e}")
        return context_md

    @staticmethod
    async def attach_podcast_audio(task_desc: str) -> str:
        """Generates TTS audio from the task description and appends the URL."""
        try:
            from src.server.services.settings_service import SettingsService
            from src.server.services.text_to_speech_service import text_to_speech_service
            from src.server.utils import get_supabase_client

            supabase = get_supabase_client()
            settings = SettingsService(supabase)

            raw_settings = settings.get_all_settings()
            try:
                config = TTSConfig.model_validate(raw_settings)
            except Exception as e:
                logger.warning(f"Failed to parse TTSConfig, falling back to defaults: {e}")
                config = TTSConfig()

            tts_limit = config.tts_truncation_limit

            logger.info("🎙️ ReportEnrichmentService: Generating TTS Podcast...")
            clean_text = task_desc.replace("*", "").replace("#", "")
            success, result = await text_to_speech_service.generate_audio(clean_text[:tts_limit])

            if success and isinstance(result, bytes):
                import uuid
                filename = f"podcast_{uuid.uuid4().hex[:8]}.wav"
                try:
                    # Upload to existing archon_documents bucket
                    supabase.storage.from_("archon_documents").upload(
                        path=filename,
                        file=result,
                        file_options={"content-type": "audio/wav"}
                    )
                    audio_url_res = supabase.storage.from_("archon_documents").create_signed_url(filename, 604800)
                    audio_url = audio_url_res.get("signedURL") or audio_url_res.get("signedUrl")
                    if audio_url:
                        task_desc += f"\n\n🎧 **Listen to Podcast**: [Audio Link]({audio_url})"
                    logger.info("✅ ReportEnrichmentService: TTS Podcast generated and attached.")
                except Exception as upload_err:
                    logger.error(f"❌ ReportEnrichmentService: Failed to upload TTS Podcast to Supabase: {upload_err}")
            else:
                logger.warning(f"⚠️ ReportEnrichmentService: TTS generation skipped or failed: {result}")

        except Exception as e:
            logger.error(f"❌ ReportEnrichmentService: Failed to generate TTS Podcast: {e}")
        return task_desc

    @staticmethod
    def prune_expired_podcast_audio(ttl_days: int = 14) -> int:
        """Deletes podcast audio files older than ttl_days from archon_documents storage bucket."""
        logger.info(f"🎙️ ReportEnrichmentService: Pruning expired podcast audio (older than {ttl_days} days)...")
        pruned_count = 0
        try:
            from datetime import UTC, datetime, timedelta

            from src.server.utils import get_supabase_client

            supabase = get_supabase_client()

            # List files in archon_documents
            files = supabase.storage.from_("archon_documents").list()
            if not files or not isinstance(files, list):
                logger.info("🎙️ ReportEnrichmentService: No files found in archon_documents storage.")
                return 0

            cutoff_date = datetime.now(UTC) - timedelta(days=ttl_days)
            files_to_remove: list[str] = []

            for f in files:
                if not isinstance(f, dict):
                    continue
                name = f.get("name", "")
                if not name.startswith("podcast_") or not name.endswith(".wav"):
                    continue
                created_at_str = f.get("created_at")
                if not created_at_str:
                    continue
                try:
                    file_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    if file_time < cutoff_date:
                        files_to_remove.append(name)
                except Exception as parse_err:
                    logger.warning(
                        f"ReportEnrichmentService: Failed to parse timestamp for {name}: {parse_err}"
                    )

            if files_to_remove:
                supabase.storage.from_("archon_documents").remove(files_to_remove)
                pruned_count = len(files_to_remove)
                logger.info(
                    f"✅ ReportEnrichmentService: Successfully pruned {pruned_count} expired podcast files."
                )

                # Record audit log
                from src.server.repositories.base_repository import BaseRepository

                repo = BaseRepository(supabase)
                repo.execute_query(
                    supabase.table("archon_logs").insert(  # 合法
                        {
                            "source": "storage-pruning",
                            "level": "INFO",
                            "message": f"Pruned {pruned_count} expired podcast audio files (TTL: {ttl_days}d).",
                            "details": {"pruned_count": pruned_count, "files": files_to_remove},
                        }
                    ),
                    "Failed to record storage pruning log",
                    require_data=False,
                )
            else:
                logger.info("🎙️ ReportEnrichmentService: No expired podcast files met the TTL threshold.")

        except Exception as e:
            logger.error(f"❌ ReportEnrichmentService: Failed to prune expired podcast audio: {e}")

        return pruned_count


report_enrichment_service = ReportEnrichmentService()

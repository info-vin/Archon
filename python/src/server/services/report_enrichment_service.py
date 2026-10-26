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
    def _upload_podcast_to_storage(supabase: object, filename: str, audio_bytes: bytes) -> str | None:
        """Uploads WAV audio to archon_documents bucket and returns a 7-day signed URL."""
        from typing import Any, cast

        sb = cast(Any, supabase)
        try:
            sb.storage.from_("archon_documents").upload(
                path=filename, file=audio_bytes, file_options={"content-type": "audio/wav"}
            )
            url_res = sb.storage.from_("archon_documents").create_signed_url(filename, 604800)
            signed_url = url_res.get("signedURL") or url_res.get("signedUrl")
            return str(signed_url) if signed_url else None
        except Exception as up_err:
            logger.warning(f"ReportEnrichmentService: Storage backup failed for {filename}: {up_err}")
            return None

    @staticmethod
    async def _generate_script_with_llm(prompt_key: str, default_prompt: str, source_text: str) -> str:
        """Generates a concise spoken broadcast script using the Supervisor Decision Model (3.6 Flash) with key & model fallback."""
        import re
        import uuid

        from google import genai

        from src.server.config.model_ssot import SYSTEM_MODELS
        from src.server.services.credential_service import credential_service
        from src.server.services.prompt_service import prompt_service
        from src.server.services.token_usage_service import TokenUsageService

        instruction = prompt_service.get_prompt(prompt_key, default_prompt)
        full_prompt = f"{instruction}\n\n---\n{source_text[:4000]}"

        primary_key = await credential_service.get_credential("GEMINI_API_KEY")
        backup_key = await credential_service.get_credential("GOOGLE_API_KEY")
        keys_to_try = [k for k in [primary_key, backup_key] if k]
        # Deduplicate while preserving order
        unique_keys = list(dict.fromkeys(keys_to_try))
        supervisor_model = SYSTEM_MODELS.get("SUPERVISOR_MODEL", "models/gemini-3.6-flash").split("/")[-1]
        pro_model = SYSTEM_MODELS.get("DEFAULT_PRO", "models/gemini-3.5-flash-lite").split("/")[-1]
        lite_model = SYSTEM_MODELS.get("DEFAULT_TEXT", "models/gemini-3.1-flash-lite").split("/")[-1]
        models_to_try = list(
            dict.fromkeys(
                [
                    supervisor_model,
                    "gemini-3.5-flash-lite",
                    pro_model,
                    lite_model,
                ]
            )
        )

        for model_name in models_to_try:
            for api_key in unique_keys:
                try:
                    client = genai.Client(api_key=api_key)
                    resp = await client.aio.models.generate_content(model=model_name, contents=full_prompt)
                    if resp.text and resp.text.strip():
                        usage = getattr(resp, "usage_metadata", None)
                        if usage:
                            await TokenUsageService.log_usage(
                                request_id=f"voice-script-{uuid.uuid4().hex[:8]}",
                                model=model_name,
                                provider="google",
                                input_tokens=int(usage.prompt_token_count or 0),
                                output_tokens=int(usage.candidates_token_count or 0),
                                context_type="Voice_Brief_Script",
                            )
                        return re.sub(r"[*_`#\[\]]", "", resp.text).strip()
                except Exception as e:
                    logger.warning(f"ReportEnrichmentService: Script LLM fallback ({model_name}): {e}")

        if "EN" in prompt_key:
            return (
                "Good morning. This is your Archon Executive Intelligence Briefing. "
                "Daily sales leads and marketing pipelines have been updated. "
                "Please check your dashboard for detailed metrics. Stay sharp, and make it a productive day."
            )
        fallback_clean = re.sub(r"http[s]?://\S+", "", source_text)
        fallback_clean = re.sub(r"[*_`#\[\]|]", " ", fallback_clean)
        return " ".join(fallback_clean.split())[:450]

    @staticmethod
    async def dispatch_dual_voice_briefings(summary_text: str) -> list[str]:
        """
        Generates and dispatches 2 native Telegram Voice Bubbles for the Daily Executive Summary:
        1. Mandarin Executive Brief (Puck voice)
        2. English CNN Business Anchor Flash Briefing (Fenrir voice)
        """
        import uuid

        from src.server.prompts.pm_prompts import DAILY_VOICE_BRIEF_EN, DAILY_VOICE_BRIEF_ZH
        from src.server.services.shared_constants import PromptNameEnum
        from src.server.services.system.telegram_service import telegram_service
        from src.server.services.text_to_speech_service import text_to_speech_service
        from src.server.utils import get_supabase_client

        uploaded_urls: list[str] = []
        tracks = [
            {
                "lang": "ZH",
                "prompt_key": PromptNameEnum.DAILY_VOICE_BRIEF_ZH.value,
                "default_prompt": DAILY_VOICE_BRIEF_ZH,
                "voice_name": "Puck",
                "caption": "🎙️ **【星環商業晨會】執行長重點語音速報 (Mandarin Executive Brief)**",
                "filename_prefix": "podcast_zh_",
            },
            {
                "lang": "EN",
                "prompt_key": PromptNameEnum.DAILY_VOICE_BRIEF_EN.value,
                "default_prompt": DAILY_VOICE_BRIEF_EN,
                "voice_name": "Fenrir",
                "caption": "🎙️ **【CNN Business Flash】60-Second Executive Intelligence Briefing**",
                "filename_prefix": "podcast_en_",
            },
        ]

        supabase = get_supabase_client()
        for idx, track in enumerate(tracks):
            try:
                if idx > 0:
                    await asyncio.sleep(5.0)  # 合法
                script = await ReportEnrichmentService._generate_script_with_llm(
                    track["prompt_key"], track["default_prompt"], summary_text
                )
                logger.info(f"🎙️ ReportEnrichmentService: Generating {track['lang']} TTS Voice ({len(script)} chars)...")
                success, audio_res = await text_to_speech_service.generate_audio(script, voice_name=track["voice_name"])
                if success and isinstance(audio_res, bytes):
                    filename = f"{track['filename_prefix']}{uuid.uuid4().hex[:8]}.wav"
                    await telegram_service.send_voice(voice_bytes=audio_res, caption=track["caption"], filename=filename)
                    signed_url = ReportEnrichmentService._upload_podcast_to_storage(supabase, filename, audio_res)
                    if signed_url:
                        uploaded_urls.append(f"[{track['lang']} Audio]({signed_url})")
                else:
                    logger.warning(f"⚠️ ReportEnrichmentService: {track['lang']} TTS skipped/failed: {audio_res}")
            except Exception as track_err:
                logger.error(f"❌ ReportEnrichmentService: Error in {track['lang']} voice pipeline: {track_err}")

        return uploaded_urls

    @staticmethod
    async def trigger_emergency_voice_alert(incident_text: str) -> bool:
        """Dispatches a high-priority Telegram Voice Bubble for critical system emergencies (max 3 calls/day)."""
        from datetime import UTC, datetime

        from src.server.prompts.pm_prompts import EMERGENCY_VOICE_ALERT
        from src.server.repositories.base_repository import BaseRepository
        from src.server.services.shared_constants import PromptNameEnum
        from src.server.services.system.telegram_service import telegram_service
        from src.server.services.text_to_speech_service import text_to_speech_service
        from src.server.utils import get_supabase_client

        try:
            supabase = get_supabase_client()
            repo = BaseRepository(supabase)
            today_start = datetime.now(UTC).strftime("%Y-%m-%dT00:00:00Z")
            try:
                _, log_res = repo.execute_query(
                    supabase.table("archon_logs")  # 合法
                    .select("id")
                    .eq("source", "emergency-voice-alert")
                    .gte("created_at", today_start),
                    "Check emergency voice alert count",
                    require_data=False,
                )
                if len(log_res.get("data") or []) >= 3:
                    logger.warning("🎙️ ReportEnrichmentService: Daily emergency voice cap (3/3) reached. Skipping TTS.")
                    return False
            except Exception:
                pass

            script = await ReportEnrichmentService._generate_script_with_llm(
                PromptNameEnum.EMERGENCY_VOICE_ALERT.value, EMERGENCY_VOICE_ALERT, incident_text
            )
            success, audio_res = await text_to_speech_service.generate_audio(script[:300], voice_name="Kore")
            if success and isinstance(audio_res, bytes):
                sent = await telegram_service.send_voice(
                    voice_bytes=audio_res,
                    caption=f"🚨 **【緊急系統語音告警】**\n{incident_text[:200]}",
                    filename="emergency_alert.wav",
                )
                try:
                    repo.execute_query(
                        supabase.table("archon_logs").insert(  # 合法
                            {
                                "source": "emergency-voice-alert",
                                "level": "ALERT",
                                "message": f"Dispatched emergency voice alert: {incident_text[:120]}",
                            }
                        ),
                        "Record emergency voice alert log",
                        require_data=False,
                    )
                except Exception:
                    pass
                return sent
        except Exception as e:
            logger.error(f"❌ ReportEnrichmentService: Emergency voice alert failed: {e}")
        return False

    @staticmethod
    async def attach_podcast_audio(task_desc: str) -> str:
        """Generates TTS audio from the task description and appends the signed storage URL."""
        try:
            import uuid

            from src.server.services.settings_service import SettingsService
            from src.server.services.text_to_speech_service import text_to_speech_service
            from src.server.utils import get_supabase_client

            supabase = get_supabase_client()
            raw_settings = SettingsService(supabase).get_all_settings()
            try:
                config = TTSConfig.model_validate(raw_settings)
            except Exception as e:
                logger.warning(f"Failed to parse TTSConfig, falling back to defaults: {e}")
                config = TTSConfig()

            logger.info("🎙️ ReportEnrichmentService: Generating TTS Podcast...")
            clean_text = task_desc.replace("*", "").replace("#", "")
            success, result = await text_to_speech_service.generate_audio(clean_text[: config.tts_truncation_limit])

            if success and isinstance(result, bytes):
                filename = f"podcast_{uuid.uuid4().hex[:8]}.wav"
                audio_url = ReportEnrichmentService._upload_podcast_to_storage(supabase, filename, result)
                if audio_url:
                    task_desc += f"\n\n🎧 **Listen to Podcast**: [Audio Link]({audio_url})"
                logger.info("✅ ReportEnrichmentService: TTS Podcast generated and attached.")
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

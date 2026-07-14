"""
Report Enrichment Service
Handles optional high-value additions to reports like Nexus Oracle insights and TTS Podcast generation.
"""

from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)

class ReportEnrichmentService:
    @staticmethod
    async def inject_nexus_oracle_insights(context_md: str) -> str:
        """Invokes NexusOracleAgent and appends its insights to the context."""
        logger.info("🔮 ReportEnrichmentService: Invoking NexusOracleAgent for high-level insights...")
        try:
            from src.agents.nexus_oracle_agent import NexusDependencies, NexusOracleAgent
            oracle = NexusOracleAgent()
            oracle_res = await oracle.run(
                "Please provide a strategic overview of the current system and business state, focusing on 104 data trends.",
                deps=NexusDependencies()
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
            logger.error(f"❌ ReportEnrichmentService: Failed to get Nexus Oracle insights: {e}")
        return context_md

    @staticmethod
    async def attach_podcast_audio(task_desc: str) -> str:
        """Generates TTS audio from the task description and appends the URL."""
        try:
            from src.server.services.text_to_speech_service import text_to_speech_service
            logger.info("🎙️ ReportEnrichmentService: Generating TTS Podcast...")
            clean_text = task_desc.replace("*", "").replace("#", "")
            audio_url = await text_to_speech_service.generate_audio(clean_text[:4000])
            if audio_url:
                task_desc += f"\n\n🎧 **Listen to Podcast**: [Audio Link]({audio_url})"
                logger.info("✅ ReportEnrichmentService: TTS Podcast generated and attached.")
        except Exception as e:
            logger.error(f"❌ ReportEnrichmentService: Failed to generate TTS Podcast: {e}")
        return task_desc

report_enrichment_service = ReportEnrichmentService()

"""
MetaTwinService - Dynamic internal monitoring and self-healing loop for AI Agents.
"""

import logging
from datetime import UTC, datetime, timedelta

from ...config.logfire_config import get_logger
from ...utils import get_supabase_client

logger = get_logger(__name__)


class MetaTwinService:
    """
    Self-healing orchestrator for the Archon Agent ecosystem.
    Audits agent parameters dynamically and executes fallback actions.
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    async def run_telemetry_audit(self) -> dict:
        """
        Scans agent execution logs and statistics to identify failures (e.g., rate limits, loops).
        Returns a summary of diagnoses and corrective actions taken.
        """
        logger.info("MetaTwin: Starting system telemetry and agent-health audit...")
        one_hour_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        
        # 1. Fetch recent agent errors
        try:
            logs_res = (
                self.supabase.table("archon_logs")
                .select("id, source, message, level, details, created_at")
                .gt("created_at", one_hour_ago)
                .execute()
            )
            logs = logs_res.data or []
        except Exception as e:
            logger.error(f"MetaTwin: Failed to query archon_logs: {e}")
            logs = []

        diagnoses = []
        corrections = []

        # Analyze errors per agent
        agent_errors: dict[str, list[dict]] = {}
        for log in logs:
            source = log.get("source", "system").lower()
            if log.get("level") == "ERROR" or "rate limit" in log.get("message", "").lower():
                agent_errors.setdefault(source, []).append(log)

        # 2. Diagnose & Heal
        for agent_name, errors in agent_errors.items():
            error_count = len(errors)
            rate_limit_hits = sum(1 for e in errors if "429" in e.get("message", "") or "rate limit" in e.get("message", "").lower())
            
            # Scenario A: Rate Limit Risk (Multiple 429 hits)
            if rate_limit_hits >= 3:
                diagnoses.append({
                    "agent": agent_name,
                    "issue": "RATE_LIMIT_RISK",
                    "reason": f"Detected {rate_limit_hits} rate limit errors in the last hour."
                })
                
                # Apply Actuator: Switch to fallback model
                fallback_success = await self.switch_model_to_fallback(agent_name, "models/gemini-3.1-flash-lite")
                if fallback_success:
                    corrections.append({
                        "agent": agent_name,
                        "action": "MODEL_SWAP",
                        "details": "Swapped DEFAULT_PRO model to DEFAULT_TEXT (Lite) fallback."
                    })
                    
            # Scenario B: Stuck in loop / Infinite calls (High error count)
            elif error_count >= 5:
                diagnoses.append({
                    "agent": agent_name,
                    "issue": "STUCK_IN_LOOP",
                    "reason": f"Detected high error frequency ({error_count} errors) suggesting execution loop."
                })
                
                # Apply Actuator: Throttle concurrency / Cooldown
                throttle_success = await self.throttle_concurrency(agent_name, 1)
                if throttle_success:
                    corrections.append({
                        "agent": agent_name,
                        "action": "THROTTLE_CONCURRENCY",
                        "details": "Conformed execution rate limit to 1 concurrent request."
                    })

        # Log audit outcomes to archon_logs as system trace
        if corrections:
            try:
                self.supabase.table("archon_logs").insert({
                    "level": "INFO",
                    "source": "MetaTwinService",
                    "type": "system",
                    "message": f"Self-healing executed: {len(corrections)} corrections applied.",
                    "details": {"diagnoses": diagnoses, "corrections": corrections}
                }).execute()
            except Exception as e:
                logger.error(f"MetaTwin: Failed to insert audit outcome log: {e}")

        return {
            "status": "completed",
            "diagnoses_count": len(diagnoses),
            "corrections_count": len(corrections),
            "diagnoses": diagnoses,
            "corrections": corrections
        }

    async def switch_model_to_fallback(self, agent_name: str, fallback_model: str) -> bool:
        """
        Actuator: Swaps active system models dynamically to prevent further rate limits.
        """
        logger.info(f"MetaTwin: Swapping agent {agent_name} model to {fallback_model}")
        try:
            from ...config.model_ssot import SYSTEM_MODELS
            # Update physical models mapping in memory
            SYSTEM_MODELS["DEFAULT_PRO"] = fallback_model
            
            # Persist setting to DB so it propagates
            await self.supabase.table("archon_settings").upsert({
                "key": f"MODEL_OVERRIDE_{agent_name.upper()}",
                "value": fallback_model,
                "description": f"Auto-Healing Model Override by MetaTwin at {datetime.now(UTC).isoformat()}"
            }).execute()
            return True
        except Exception as e:
            logger.error(f"MetaTwin: Model override failed for {agent_name}: {e}")
            return False

    async def throttle_concurrency(self, agent_name: str, new_limit: int) -> bool:
        """
        Actuator: Dynamically scales down concurrency limits for the specified agent.
        """
        logger.info(f"MetaTwin: Throttling agent {agent_name} concurrency limit to {new_limit}")
        try:
            await self.supabase.table("archon_settings").upsert({
                "key": f"CRAWL_CONCURRENT_MAX_{agent_name.upper()}",
                "value": str(new_limit),
                "description": f"Auto-Healing Concurrency Limit by MetaTwin at {datetime.now(UTC).isoformat()}"
            }).execute()
            return True
        except Exception as e:
            logger.error(f"MetaTwin: Throttling failed for {agent_name}: {e}")
            return False


# Singleton Instance
meta_twin_service = MetaTwinService()

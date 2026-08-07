from ..config.logfire_config import get_logger

logger = get_logger(__name__)


class GuardrailService:
    """
    Service for validating AI inputs and auditing AI outputs.
    Acts as a safety layer to prevent hallucinations, profanity, or policy violations.
    """

    # Basic keyword blocklist (In a real app, this might come from DB or external service)
    FORBIDDEN_KEYWORDS = {
        "competitor_x",
        "illegal",
        "confidential",
        "internal_only",
        "password",
        "secret",
        "hack",
        "exploit",
    }

    @classmethod
    def validate_input(cls, text: str) -> tuple[bool, str | None]:
        """
        Check if the input text contains any forbidden keywords.
        Returns: (is_valid, error_message)
        """
        if not text:
            return True, None

        text_lower = text.lower()
        for word in cls.FORBIDDEN_KEYWORDS:
            if word in text_lower:
                logger.warning(f"Guardrail: Input blocked due to forbidden keyword '{word}'")

                # Log to Ethics Table (Fire and forget)
                try:
                    from ..utils import get_supabase_client
                    from ..repositories.base_repository import BaseRepository

                    supabase = get_supabase_client()
                    base_repo = BaseRepository(supabase)
                    base_repo.execute_query(
                        supabase.table("archon_ethics_events").insert( # 合法
                            {
                                "severity": "high",
                                "event_type": "policy_violation",
                                "description": f"Input contained forbidden keyword: {word}",
                                "raw_input": text,
                                "created_at": "now()",
                            }
                        ),
                        error_context="Failed to log ethics event"
                    )
                except Exception as e:
                    logger.error(f"Failed to log ethics event: {e}")

                return False, f"Input contains forbidden keyword: {word}"

        return True, None

    @classmethod
    def audit_output(cls, generated_text: str, context_text: str = "") -> tuple[bool, str | None]:
        """
        Audit the generated text for quality issues (e.g., hallucinations).
        For Phase 4.5, we implement a basic heuristic check.

        Future: Use a lighter LLM (e.g., gpt-3.5-turbo) to verify facts against context.
        """
        if not generated_text:
            return False, "Generated text is empty."

        # Basic Check: If context is provided, ensure at least some overlap?
        # This is tricky for creative writing.
        # For now, we enforce a length check and ensure no "I am an AI" leakage if tone is professional.

        if "i am an ai language model" in generated_text.lower():
            logger.warning("Guardrail: Output blocked due to AI disclosure leakage")

            # Log to Ethics Table
            try:
                from ..utils import get_supabase_client
                from ..repositories.base_repository import BaseRepository

                supabase = get_supabase_client()
                base_repo = BaseRepository(supabase)
                base_repo.execute_query(
                    supabase.table("archon_ethics_events").insert( # 合法
                        {
                            "severity": "medium",
                            "event_type": "hallucination",
                            "description": "AI Output contained generic disclosure (potential hallucination/leakage)",
                            "raw_input": generated_text[:500],  # Store partial output
                            "created_at": "now()",
                        }
                    ),
                    error_context="Failed to log ethics event"
                )
            except Exception as e:
                logger.error(f"Failed to log ethics event: {e}")

            return False, "Output contains generic AI disclosure."

        return True, None

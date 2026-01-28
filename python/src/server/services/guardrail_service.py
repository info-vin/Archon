
from typing import List, Optional
from ..config.logfire_config import get_logger

logger = get_logger(__name__)

class GuardrailService:
    """
    Service for validating AI inputs and auditing AI outputs.
    Acts as a safety layer to prevent hallucinations, profanity, or policy violations.
    """

    # Basic keyword blocklist (In a real app, this might come from DB or external service)
    FORBIDDEN_KEYWORDS = {
        "competitor_x", "illegal", "confidential", "internal_only", 
        "password", "secret", "hack", "exploit"
    }

    @classmethod
    def validate_input(cls, text: str) -> tuple[bool, Optional[str]]:
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
                return False, f"Input contains forbidden keyword: {word}"
        
        return True, None

    @classmethod
    def audit_output(cls, generated_text: str, context_text: str = "") -> tuple[bool, Optional[str]]:
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
             return False, "Output contains generic AI disclosure."

        return True, None

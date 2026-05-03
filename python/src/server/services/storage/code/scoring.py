"""
Handles the evaluation and scoring of code blocks for RAG value weight.
"""

from typing import Any


def score_block(block: dict[str, Any]) -> float:
    """Calculates a heuristic score for the quality and RAG-value of a code block."""
    score = 0.0
    if block.get("language") and block["language"] not in ["", "text", "plaintext"]:
        score += 10

    code_content = block.get("code", "")
    score += len(code_content) * 0.01

    context_before_len = len(block.get("context_before", ""))
    context_after_len = len(block.get("context_after", ""))
    score += (context_before_len + context_after_len) * 0.005

    full_context_lower = block.get("full_context", "").lower()
    if "python 3.10" in full_context_lower:
        score += 5
    elif "annotated" in code_content.lower():
        score += 3

    return score

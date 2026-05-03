"""
Code Extraction Engine for Code Storage Service (Phase 4.6.12 Hardening)

Handles the logic for extracting, normalizing, and deduplicating code blocks
from markdown content. Acts as the main orchestrator/facade for the
code extraction domain.
"""

from typing import Any

from .deduplication import deduplicate_code_blocks
from .extractors import extract_code_blocks_logic as _extract_code_blocks_logic


def extract_code_blocks_logic(markdown_content: str, min_length: int | None = None) -> list[dict[str, Any]]:
    """
    Extracts and deduplicates code blocks from markdown content.
    Delegates parsing to extractors.py and deduplication to deduplication.py.
    """
    # 1. Extract raw blocks
    raw_blocks = _extract_code_blocks_logic(markdown_content, min_length)

    if not raw_blocks:
        return []

    # 2. Deduplicate similar blocks
    return deduplicate_code_blocks(raw_blocks)

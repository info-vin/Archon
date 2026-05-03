"""
Code deduplication algorithms and similarity heuristics.
"""

import re
from difflib import SequenceMatcher
from typing import Any

from .scoring import score_block

# Pre-compiled regular expressions for code normalization
_WHITESPACE_RE = re.compile(r"\s+")
_TYPING_EXT_RE = re.compile(r"from typing_extensions import")
_TYPING_ANN_RE = re.compile(r"from typing import Annotated[^,\n]*,?")
_TYPING_EXT_ANN_RE = re.compile(r"from typing_extensions import Annotated[^,\n]*,?")
_ANN_WRAP_RE = re.compile(r"Annotated\[\s*([^,\]]+)[^]]*\]")
_FASTAPI_PARAM_RE = re.compile(r":\s*Annotated\[[^\]]+\]\s*=")
_TRAILING_COMMA_PAREN_RE = re.compile(r",\s*\)")
_TRAILING_COMMA_BRACKET_RE = re.compile(r",\s*]")

def normalize_code_for_comparison(code: str) -> str:
    """Normalizes code string to improve similarity matching."""
    normalized = _WHITESPACE_RE.sub(" ", code.strip())
    normalized = _TYPING_EXT_RE.sub("from typing import", normalized)
    normalized = _TYPING_ANN_RE.sub("", normalized)
    normalized = _TYPING_EXT_ANN_RE.sub("", normalized)
    normalized = _ANN_WRAP_RE.sub(r"\1", normalized)
    normalized = _FASTAPI_PARAM_RE.sub("=", normalized)
    normalized = _TRAILING_COMMA_PAREN_RE.sub(")", normalized)
    normalized = _TRAILING_COMMA_BRACKET_RE.sub("]", normalized)
    return normalized

def select_best_code_variant(similar_blocks: list[dict[str, Any]]) -> dict[str, Any]:
    """Selects the highest quality code block from a group of similar variants."""
    if len(similar_blocks) == 1:
        return similar_blocks[0]

    best_block = max(similar_blocks, key=score_block)
    variant_count = len(similar_blocks)

    if variant_count > 1:
        languages = [block.get("language", "") for block in similar_blocks if block.get("language")]
        unique_languages = list(set(filter(None, languages)))
        best_block["consolidated_variants"] = variant_count
        if unique_languages:
            best_block["variant_languages"] = unique_languages

    return best_block

def deduplicate_code_blocks(code_blocks: list[dict[str, Any]], similarity_threshold: float = 0.85) -> list[dict[str, Any]]:
    """Deduplicates a list of code blocks based on semantic similarity."""
    if not code_blocks:
        return []

    grouped_blocks = []
    processed_indices = set()

    # Pre-calculate normalized code strings to avoid O(N^2) repeated normalizations
    normalized_codes = [normalize_code_for_comparison(b["code"]) for b in code_blocks]

    # Pre-calculate lengths to allow O(1) upper-bound ratio checks before expensive SequenceMatcher logic
    norm_lengths = [len(norm) for norm in normalized_codes]

    for idx, block1 in enumerate(code_blocks):
        if idx in processed_indices:
            continue
        similar_group = [block1]
        processed_indices.add(idx)

        norm1 = normalized_codes[idx]
        len1 = norm_lengths[idx]

        for jdx, block2 in enumerate(code_blocks):
            if jdx <= idx or jdx in processed_indices:
                continue

            len2 = norm_lengths[jdx]

            # PERFORMANCE: O(1) fast upper-bound length ratio check
            if len1 + len2 > 0 and (2.0 * min(len1, len2) / (len1 + len2)) < similarity_threshold:
                continue

            norm2 = normalized_codes[jdx]

            # PERFORMANCE: Utilize SequenceMatcher heuristic guards
            matcher = SequenceMatcher(None, norm1, norm2)
            if (
                matcher.real_quick_ratio() >= similarity_threshold
                and matcher.quick_ratio() >= similarity_threshold
                and matcher.ratio() >= similarity_threshold
            ):
                similar_group.append(block2)
                processed_indices.add(jdx)

        grouped_blocks.append(select_best_code_variant(similar_group))

    return grouped_blocks

"""
Code Extraction Engine for Code Storage Service (Phase 4.6.12 Hardening)

Handles the logic for extracting, normalizing, and deduplicating code blocks
from markdown content using regex and similarity heuristics.
"""

import os
import re
from difflib import SequenceMatcher
from typing import Any, cast

from src.server.config.logfire_config import search_logger

# Pre-compiled regular expressions for code normalization (Optimized by Jules)
_WHITESPACE_RE = re.compile(r"\s+")
_TYPING_EXT_RE = re.compile(r"from typing_extensions import")
_TYPING_ANN_RE = re.compile(r"from typing import Annotated[^,\n]*,?")
_TYPING_EXT_ANN_RE = re.compile(r"from typing_extensions import Annotated[^,\n]*,?")
_ANN_WRAP_RE = re.compile(r"Annotated\[\s*([^,\]]+)[^]]*\]")
_FASTAPI_PARAM_RE = re.compile(r":\s*Annotated\[[^\]]+\]\s*=")
_TRAILING_COMMA_PAREN_RE = re.compile(r",\s*\)")
_TRAILING_COMMA_BRACKET_RE = re.compile(r",\s*]")

# Evaluation Indicators
_DOC_INDICATORS = [
    ("this ", "that ", "these ", "those ", "the "),
    ("is ", "are ", "was ", "were ", "will ", "would "),
    ("to ", "from ", "with ", "for ", "and ", "or "),
    "for example:",
    "note:",
    "warning:",
    "important:",
    "description:",
    "usage:",
    "parameters:",
    "returns:",
    ". ",
    "? ",
    "! ",
]

_DOC_INDICATOR_WORDS = [w for ind in _DOC_INDICATORS if isinstance(ind, tuple) for w in ind]
_DOC_INDICATOR_STRINGS = [ind for ind in _DOC_INDICATORS if isinstance(ind, str)]

_CODE_PATTERNS = [
    "=",
    "(",
    ")",
    "{",
    "}",
    "[",
    "]",
    ";",
    "function",
    "def",
    "class",
    "import",
    "export",
    "const",
    "let",
    "var",
    "return",
    "if",
    "for",
    "->",
    "=>",
    "==",
    "!=",
    "<=",
    ">=",
]

_DIAGRAM_INDICATORS = [
    "┌",
    "┐",
    "└",
    "┘",
    "│",
    "─",
    "├",
    "┤",
    "┬",
    "┴",
    "┼",
    "+-+",
    "|_|",
    "___",
    "...",
    "→",
    "←",
    "↑",
    "↓",
    "⟶",
    "⟵",
]


def _normalize_code_for_comparison(code: str) -> str:
    normalized = _WHITESPACE_RE.sub(" ", code.strip())
    normalized = _TYPING_EXT_RE.sub("from typing import", normalized)
    normalized = _TYPING_ANN_RE.sub("", normalized)
    normalized = _TYPING_EXT_ANN_RE.sub("", normalized)
    normalized = _ANN_WRAP_RE.sub(r"\1", normalized)
    normalized = _FASTAPI_PARAM_RE.sub("=", normalized)
    normalized = _TRAILING_COMMA_PAREN_RE.sub(")", normalized)
    normalized = _TRAILING_COMMA_BRACKET_RE.sub("]", normalized)
    return normalized


def _select_best_code_variant(similar_blocks: list[dict[str, Any]]) -> dict[str, Any]:
    if len(similar_blocks) == 1:
        return similar_blocks[0]

    def score_block(block):
        score = 0.0
        if block.get("language") and block["language"] not in ["", "text", "plaintext"]:
            score += 10
        score += len(block["code"]) * 0.01
        context_before_len = len(block.get("context_before", ""))
        context_after_len = len(block.get("context_after", ""))
        score += (context_before_len + context_after_len) * 0.005
        if "python 3.10" in block.get("full_context", "").lower():
            score += 5
        elif "annotated" in block.get("code", "").lower():
            score += 3
        return score

    best_block = max(similar_blocks, key=score_block)
    variant_count = len(similar_blocks)
    if variant_count > 1:
        languages = [block.get("language", "") for block in similar_blocks if block.get("language")]
        unique_languages = list(set(filter(None, languages)))
        best_block["consolidated_variants"] = variant_count
        if unique_languages:
            best_block["variant_languages"] = unique_languages
    return best_block


def extract_code_blocks_logic(markdown_content: str, min_length: int | None = None) -> list[dict[str, Any]]:
    """
    Core extraction engine logic.
    Restored with FULL Jules Performance Optimizations.
    """
    try:
        from src.server.services.credential_service import credential_service

        def _get_setting_fallback(key: str, default: str) -> str:
            if credential_service._cache_initialized and key in credential_service._cache:
                return cast(str, credential_service._cache[key])
            return os.getenv(key, default)

        if min_length is None:
            min_length = int(_get_setting_fallback("MIN_CODE_BLOCK_LENGTH", "250"))

        max_length = int(_get_setting_fallback("MAX_CODE_BLOCK_LENGTH", "5000"))
        enable_prose_filtering = _get_setting_fallback("ENABLE_PROSE_FILTERING", "true").lower() == "true"
        max_prose_ratio = float(_get_setting_fallback("MAX_PROSE_RATIO", "0.15"))
        min_code_indicators = int(_get_setting_fallback("MIN_CODE_INDICATORS", "3"))
        enable_diagram_filtering = _get_setting_fallback("ENABLE_DIAGRAM_FILTERING", "true").lower() == "true"
        context_window_size = int(_get_setting_fallback("CONTEXT_WINDOW_SIZE", "1000"))

    except Exception as e:
        search_logger.warning(f"Failed to get code extraction settings: {e}, using defaults")
        if min_length is None:
            min_length = 250
        max_length, enable_prose_filtering, max_prose_ratio = 5000, True, 0.15
        min_code_indicators, enable_diagram_filtering, context_window_size = 3, True, 1000

    code_blocks = []
    content = markdown_content.strip()

    if content.startswith("```"):
        first_line = content.split("\n")[0] if "\n" in content else content[:10]
        if re.match(r"^```[A-Z]`$", first_line):
            inner_content = content[5:-3] if content.endswith("```") else content[5:]
            return extract_code_blocks_logic(inner_content, min_length)

    parts = markdown_content.split("```")
    backtick_positions = []
    if len(parts) > 1:
        current_pos = 0
        for i in range(len(parts) - 1):
            current_pos += len(parts[i])
            backtick_positions.append(current_pos)
            current_pos += 3

    i = 0
    while i < len(backtick_positions) - 1:
        start_pos, end_pos = backtick_positions[i], backtick_positions[i + 1]
        code_section = markdown_content[start_pos + 3 : end_pos]
        lines = code_section.split("\n", 1)
        if len(lines) > 1:
            first_line = lines[0].strip()
            if first_line and " " not in first_line and len(first_line) < 20:
                language, code_content = first_line.lower(), lines[1]
            else:
                language, code_content = "", code_section
        else:
            language, code_content = "", code_section

        if len(code_content) < min_length or len(code_content) > max_length:
            i += 2
            continue

        # PERFORMANCE: Pre-strip and filter non-empty lines once (Restored from Jules)
        non_empty_lines = [line for line in code_content.split("\n") if line and not line.isspace()]

        if not language or language in ["text", "plaintext", "txt"]:
            code_lower = code_content.lower()

            # PERFORMANCE: Replaced sum(1 for ...) with standard for loop
            # to avoid generator object creation overhead in hot paths
            doc_score = 0
            for w in _DOC_INDICATOR_WORDS:
                if w in code_lower:
                    doc_score += 1

            for s in _DOC_INDICATOR_STRINGS:
                if s in code_lower:
                    doc_score += 2

            if enable_prose_filtering:
                words = code_content.split()
                if words and (doc_score / len(words)) > max_prose_ratio:
                    i += 2
                    continue

            # PERFORMANCE: Replaced sum(1 for ...) with standard for loop
            code_pattern_count = 0
            for p in _CODE_PATTERNS:
                if p in code_content:
                    code_pattern_count += 1

            if code_pattern_count < min_code_indicators and len(non_empty_lines) > 5:
                i += 2
                continue

            if enable_diagram_filtering:
                # Optimized diagram check using non_empty_lines
                special_char_lines = 0
                for line in non_empty_lines[:10]:
                    if line:
                        # PERFORMANCE: Replaced sum(1 for ...) with standard for loop
                        special_chars = 0
                        for c in line:
                            if not c.isalnum() and not c.isspace():
                                special_chars += 1
                        if special_chars / len(line) > 0.7:
                            special_char_lines += 1

                # PERFORMANCE: Replaced sum(1 for ...) with standard for loop
                diagram_indicator_count = 0
                for ind in _DIAGRAM_INDICATORS:
                    if ind in code_content:
                        diagram_indicator_count += 1

                if (special_char_lines >= 3 or diagram_indicator_count >= 5) and code_pattern_count < 5:
                    i += 2
                    continue

        context_start = max(0, start_pos - context_window_size)
        context_before = markdown_content[context_start:start_pos].strip()
        context_end = min(len(markdown_content), end_pos + 3 + context_window_size)
        context_after = markdown_content[end_pos + 3 : context_end].strip()

        stripped_code = code_content.strip()
        code_blocks.append(
            {
                "code": stripped_code,
                "language": language,
                "context_before": context_before,
                "context_after": context_after,
                "full_context": f"{context_before}\n\n{stripped_code}\n\n{context_after}",
            }
        )
        i += 2

    if not code_blocks:
        return code_blocks

    similarity_threshold, grouped_blocks, processed_indices = 0.85, [], set()

    # Pre-calculate normalized code strings to avoid O(N^2) repeated normalizations
    normalized_codes = [_normalize_code_for_comparison(b["code"]) for b in code_blocks]
    # PERFORMANCE: Pre-calculate lengths to allow O(1) upper-bound ratio checks before expensive SequenceMatcher logic
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

            # PERFORMANCE: Utilize SequenceMatcher heuristic guards real_quick_ratio() and quick_ratio()
            # to short-circuit expensive .ratio() evaluations during O(N^2) similarity checks
            matcher = SequenceMatcher(None, norm1, norm2)
            if (
                matcher.real_quick_ratio() >= similarity_threshold
                and matcher.quick_ratio() >= similarity_threshold
                and matcher.ratio() >= similarity_threshold
            ):
                similar_group.append(block2)
                processed_indices.add(jdx)

        grouped_blocks.append(_select_best_code_variant(similar_group))
    return grouped_blocks

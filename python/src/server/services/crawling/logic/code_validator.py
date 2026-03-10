"""
Code Quality Validator Logic
Ensures extracted content is meaningful programming code.
"""

import re

from src.server.config.logfire_config import safe_logfire_info

from .constants import CODE_INDICATORS, COMMENT_PATTERNS, LANGUAGE_PATTERNS, PROSE_INDICATORS


async def validate_code_quality(
    code: str,
    language: str,
    is_diagram_filtering_enabled: bool,
    min_code_indicators: int,
    is_prose_filtering_enabled: bool,
    max_prose_ratio: float
) -> bool:
    """Enhanced validation to ensure extracted content is actual code."""
    if not code or len(code.strip()) < 20:
        return False

    if is_diagram_filtering_enabled:
        if language.lower() in ["mermaid", "plantuml", "graphviz", "dot", "diagram"]:
            safe_logfire_info(f"Skipping diagram language: {language}")
            return False

    # Check for poor extraction patterns
    bad_patterns = [
        r"\b(from|import|def|class|if|for|while|return)(?=[a-z])",
        r"&[lg]t;|&amp;|&quot;|&#\d+;",
        r"<[^>]{50,}>",
        r"(<span[^>]*>){5,}",
        r"[^\s]{200,}",
    ]
    for pattern in bad_patterns:
        if re.search(pattern, code):
            safe_logfire_info(f"Code failed quality check: pattern '{pattern}' found")
            return False

    indicator_count = 0
    for _name, pattern in CODE_INDICATORS.items():
        if re.search(pattern, code):
            indicator_count += 1

    if indicator_count < min_code_indicators:
        safe_logfire_info(f"Code has insufficient indicators: {indicator_count} found")
        return False

    lines = code.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    if not non_empty_lines:
        return False

    comment_lines = 0
    for line in lines:
        for pattern in COMMENT_PATTERNS:
            if re.match(pattern, line.strip()):
                comment_lines += 1
                break

    if non_empty_lines and comment_lines / len(non_empty_lines) > 0.7:
        safe_logfire_info(f"Code is mostly comments: {comment_lines}/{len(non_empty_lines)} lines")
        return False

    if language.lower() in LANGUAGE_PATTERNS:
        lang_info = LANGUAGE_PATTERNS[language.lower()]
        lang_indicators = lang_info.get("min_indicators", [])

        # PERFORMANCE: Replaced sum(1 for ...) with standard for loop to avoid
        # repeated code.lower() evaluations which are O(N) allocations
        code_lower = code.lower()
        found_lang_indicators = 0
        for indicator in lang_indicators:
            if indicator in code_lower:
                found_lang_indicators += 1

        if found_lang_indicators < 2:
            safe_logfire_info(f"Code lacks {language} indicators")
            return False

    if len(non_empty_lines) < 3:
        return False

    # PERFORMANCE: Replaced sum(1 for ...) with standard for loop
    very_long_lines = 0
    for line in lines:
        if len(line) > 300:
            very_long_lines += 1

    if len(lines) > 0 and very_long_lines > len(lines) * 0.5:
        safe_logfire_info("Code has too many very long lines")
        return False

    if is_prose_filtering_enabled:
        prose_score = 0
        words = code.split()
        word_count = len(words)
        for pattern in PROSE_INDICATORS:
            prose_score += len(re.findall(pattern, code, re.IGNORECASE))
        if word_count > 0 and prose_score / word_count > max_prose_ratio:
            safe_logfire_info(f"Code appears to be prose: ratio={prose_score/word_count}")
            return False

    return True

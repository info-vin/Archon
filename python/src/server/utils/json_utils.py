"""
Robust JSON parsing utilities for LLM responses.
"""

import json
import re
from typing import Any, cast


def safe_json_loads(text: str) -> dict[str, Any]:
    """
    Safely parses JSON from LLM responses with multiple layers of defense:
    1. Removes Markdown code fences (```json ... ```).
    2. Cleans truly invalid control characters (ASCII 0-31 except allowed ones).
    3. Uses strict=False to allow unescaped newlines in string values.
    """
    if not text:
        return {}

    # 1. Strip Markdown Code Blocks
    # Matches ```json { ... } ``` or just ``` { ... } ```
    cleaned = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", text, flags=re.DOTALL)
    cleaned = cleaned.strip()

    # 2. Clean truly invalid control characters
    # JSON spec (RFC 8259) prohibits ASCII 0-31 within strings unless escaped.
    # However, many LLMs output raw newlines, tabs, or carriage returns.
    # We remove other dangerous ones like null (\\x00), etc., but keep \\n, \\r, \\t
    # so that strict=False can handle them.
    # Pattern: Matches 0-31 except 9(tab), 10(nl), 13(cr)
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]", "", cleaned)

    # 3. Parse with non-strict mode
    try:
        return cast(dict[str, Any], json.loads(cleaned, strict=False))
    except json.JSONDecodeError as e:
        # Final stand: try to find the first '{' and last '}'
        # This handles cases where LLM includes conversational text around the JSON.
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            try:
                return cast(dict[str, Any], json.loads(match.group(1), strict=False))
            except json.JSONDecodeError:
                pass

        # If all fails, re-raise original error
        raise e

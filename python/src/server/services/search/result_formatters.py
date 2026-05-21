"""
Result formatters and context extractors for search results.
"""

from typing import Any


def extract_code_context(result: dict[str, Any]) -> dict[str, Any]:
    """
    Extract additional context information from a code example result.

    Args:
        result: Raw search result from database

    Returns:
        Dictionary with contextual information
    """
    context = {}

    metadata = result.get("metadata", {})
    if isinstance(metadata, dict):
        if "language" in metadata:
            context["language"] = metadata["language"]
        if "framework" in metadata:
            context["framework"] = metadata["framework"]
        if "file_path" in metadata:
            context["file_path"] = metadata["file_path"]
        if "line_start" in metadata and "line_end" in metadata:
            context["line_range"] = f"{metadata['line_start']}-{metadata['line_end']}"

    content = result.get("content", "")
    if content:
        context["content_length"] = len(content)
        context["line_count"] = content.count("\\n") + 1

    return context

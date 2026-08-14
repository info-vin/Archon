"""
Result formatters and context extractors for search results.
"""

from typing import Any, TypedDict


class CodeContext(TypedDict, total=False):
    """DTO for code extraction context."""
    language: str
    framework: str
    file_path: str
    line_range: str
    content_length: int
    line_count: int


def extract_code_context(result: dict[str, Any]) -> CodeContext:
    """
    Extract additional context information from a code example result.

    Args:
        result: Raw search result from database

    Returns:
        CodeContext with contextual information
    """
    context: CodeContext = {}

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

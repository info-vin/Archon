"""
Query analyzer for code search intent.
"""
from typing import Any

from .dictionaries.frameworks import FRAMEWORKS
from .dictionaries.languages import PROGRAMMING_LANGUAGES

CODE_KEYWORDS = [
    "function",
    "class",
    "method",
    "algorithm",
    "implementation",
    "example",
    "tutorial",
    "pattern",
    "template",
    "snippet",
    "code",
    "programming",
    "development",
    "api",
    "library",
]

def analyze_code_query(query: str) -> dict[str, Any]:
    """
    Analyze a query to determine if it's code-related and extract relevant information.

    Args:
        query: Search query to analyze

    Returns:
        Analysis results with query classification and extracted info
    """
    query_lower = query.lower()

    detected_languages = [lang for lang in PROGRAMMING_LANGUAGES if lang in query_lower]
    detected_frameworks = [fw for fw in FRAMEWORKS if fw in query_lower]
    code_indicators = [kw for kw in CODE_KEYWORDS if kw in query_lower]

    is_code_query = len(detected_languages) > 0 or len(detected_frameworks) > 0 or len(code_indicators) > 0

    return {
        "is_code_query": is_code_query,
        "confidence": min(
            1.0,
            (len(detected_languages) + len(detected_frameworks) + len(code_indicators)) * 0.3,
        ),
        "languages": detected_languages,
        "frameworks": detected_frameworks,
        "code_indicators": code_indicators,
        "enhanced_query_recommended": is_code_query,
    }

def analyze_query_for_code_search(query: str) -> dict[str, Any]:
    """
    Standalone function to analyze if a query is code-related.
    """
    return analyze_code_query(query)

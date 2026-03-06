"""
Constants for Code Extraction logic.
Includes language-specific patterns and quality indicators.
"""

LANGUAGE_PATTERNS = {
    "typescript": {
        "block_start": r"^\s*(export\s+)?(class|interface|function|const|type|enum)\s+\w+",
        "block_end": r"^\}(\s*;)?$",
        "min_indicators": [":", "{", "}", "=>", "function", "class", "interface", "type"],
    },
    "javascript": {
        "block_start": r"^\s*(export\s+)?(class|function|const|let|var)\s+\w+",
        "block_end": r"^\}(\s*;)?$",
        "min_indicators": ["function", "{", "}", "=>", "const", "let", "var"],
    },
    "python": {
        "block_start": r"^\s*(class|def|async\s+def)\s+\w+",
        "block_end": r"^\S",  # Unindented line
        "min_indicators": ["def", ":", "return", "self", "import", "class"],
    },
    "java": {
        "block_start": r"^\s*(public|private|protected)?\s*(class|interface|enum)\s+\w+",
        "block_end": r"^\}$",
        "min_indicators": ["class", "public", "private", "{", "}", ";"],
    },
    "rust": {
        "block_start": r"^\s*(pub\s+)?(fn|struct|impl|trait|enum)\s+\w+",
        "block_end": r"^\}$",
        "min_indicators": ["fn", "let", "mut", "impl", "struct", "->"],
    },
    "go": {
        "block_start": r"^\s*(func|type|struct)\s+\w+",
        "block_end": r"^\}$",
        "min_indicators": ["func", "type", "struct", "{", "}", ":="],
    },
}

CODE_INDICATORS = {
    "function_calls": r"\w+\s*\([^)]*\)",
    "assignments": r"\w+\s*=\s*.+",
    "control_flow": r"\b(if|for|while|switch|case|try|catch|except)\b",
    "declarations": r"\b(var|let|const|def|class|function|interface|type|struct|enum)\b",
    "imports": r"\b(import|from|require|include|using|use)\b",
    "brackets": r"[\{\}\[\]]",
    "operators": r"[\+\-\*\/\%\&\|\^<>=!]",
    "method_chains": r"\.\w+",
    "arrows": r"(=>|->)",
    "keywords": r"\b(return|break|continue|yield|await|async)\b",
}

COMMENT_PATTERNS = [
    r"^\s*(//|#|/\*|\*|<!--)",  # Single line comments
    r'^\s*"""',  # Python docstrings
    r"^\s*'''",  # Python docstrings alt
    r"^\s*\*\s",  # JSDoc style
]

PROSE_INDICATORS = [
    r"\b(the|this|that|these|those|is|are|was|were|will|would|should|could|have|has|had)\b",
    r"[.!?]\s+[A-Z]",  # Sentence endings followed by capital letter
    r"\b(however|therefore|furthermore|moreover|nevertheless)\b",
]

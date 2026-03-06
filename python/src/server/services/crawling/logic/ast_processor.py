"""
Code Extraction AST Processor Logic
Handles the pure parsing and cleaning of code blocks from various content types.
"""

import re


def decode_html_entities(text: str) -> str:
    """Decode common HTML entities and clean HTML tags from code."""
    if "</span><span" in text:
        text = re.sub(r"</span>", "", text)
        text = re.sub(r"<span[^>]*>", "", text)
    else:
        text = re.sub(r"</span>(?=[A-Za-z0-9])", " ", text)
        text = re.sub(r"<span[^>]*>", "", text)
    text = re.sub(r"</?[^>]+>", "", text)
    replacements = {"&lt;": "<", "&gt;": ">", "&amp;": "&", "&quot;": '"', "&#39;": "'", "&nbsp;": " ", "&#x27;": "'", "&#x2F;": "/", "&#60;": "<", "&#62;": ">"}
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    text = text.replace("\\n", "\n")
    lines = text.split("\n")
    return "\n".join([re.sub(r" +", " ", line).rstrip() for line in lines])

def clean_code_content(code: str, language: str = "") -> str:
    """Clean and fix common issues in extracted code content."""
    code = decode_html_entities(code)
    spacing_fixes = [
        (r"(\b(?:from|import|as)\b)([A-Za-z])", r"\1 \2"),
        (r"(\b(?:def|class|async|await|return|raise|yield)\b)([A-Za-z])", r"\1 \2"),
        (r"(\b(?:if|elif|else|for|while|try|except|finally|with)\b)([A-Za-z])", r"\1 \2"),
        (r"(\b(?:int|str|float|bool|list|dict|tuple|set|None|True|False)\b)([A-Za-z])", r"\1 \2"),
        (r"(\b(?:and|or|not|in|is|lambda)\b)([A-Za-z])", r"\1 \2"),
        (r"([A-Za-z_)])(\+|-|\*|/|=|<|>|%)", r"\1 \2"),
        (r"(\+|-|\*|/|=|<|>|%)([A-Za-z_(])", r"\1 \2"),
    ]
    for pattern, replacement in spacing_fixes:
        code = re.sub(pattern, replacement, code)
    if language.lower() in ["python", "py"]:
        code = re.sub(r"(\b(?:from|import)\b)(\w+)(\b(?:import)\b)", r"\1 \2 \3", code)
        code = re.sub(r"(\b(?:def|class|if|elif|else|for|while|try|except|finally|with)\b[^:]+)$", r"\1:", code, flags=re.MULTILINE)

    if code.startswith("```") and code.endswith("```"):
        lines = code.split("\n")
        if len(lines) > 2:
            code = "\n".join(lines[1:-1])
    elif code.startswith("`") and code.endswith("`"):
        code = code[1:-1]

    lines = code.split("\n")
    res = []
    for line in lines:
        stripped = line.lstrip()
        indent = line[:len(line) - len(stripped)]
        res.append(indent + re.sub(r" {2,}", " ", stripped))
    return "\n".join(res).strip()

def detect_language_from_content(code: str) -> str:
    """Heuristic language detection."""
    patterns = {
        "python": [r"\bdef\s+\w+\s*\(", r"\bclass\s+\w+", r"\bimport\s+\w+"],
        "javascript": [r"\bfunction\s+\w+\s*\(", r"\bconst\s+\w+\s*="],
        "typescript": [r"\binterface\s+\w+", r":\s*\w+\[\]", r"\btype\s+\w+\s*="],
        "java": [r"\bpublic\s+class\s+\w+", r"\bpublic\s+static\s+void\s+main"],
        "rust": [r"\bfn\s+\w+\s*\(", r"\blet\s+mut\s+\w+", r"\bimpl\s+\w+"],
        "go": [r"\bfunc\s+\w+\s*\(", r"\bpackage\s+\w+"],
    }
    scores = {}
    for lang, lang_patterns in patterns.items():
        score = sum(1 for p in lang_patterns if re.search(p, code, re.MULTILINE))
        if score > 0:
            scores[lang] = score

    if not scores:
        return ""
    return max(scores, key=lambda k: scores[k])

async def find_complete_code_block(content: str, start_pos: int, min_length: int, language: str, max_length: int, language_patterns: dict) -> tuple[str, int]:
    if start_pos + min_length > len(content):
        return content[start_pos:], len(content)

    boundary_patterns = [r"\n}\s*$", r"\n}\s*;?\s*$", r"\n\)\s*;?\s*$", r"\n\s*$\n\s*$", r"\n(?=class\s)", r"\n(?=function\s)", r"\n(?=def\s)", r"\n(?=export\s)", r"\n(?=const\s)", r"\n(?=//)", r"\n(?=#)", r"\n(?=\*)", r"\n(?=```)"]
    if language and language.lower() in language_patterns:
        pat = language_patterns[language.lower()]
        if "block_end" in pat:
            boundary_patterns.insert(0, str(pat["block_end"]))

    extended_pos = start_pos + min_length
    while extended_pos < len(content):
        lookahead = content[extended_pos:min(extended_pos + 500, len(content))]
        for pattern in boundary_patterns:
            match = re.search(pattern, lookahead, re.MULTILINE)
            if match:
                final_pos = extended_pos + match.end()
                return content[start_pos:final_pos].rstrip(), final_pos
        extended_pos += 100
        if extended_pos - start_pos > max_length:
            break
    return content[start_pos:extended_pos].rstrip(), extended_pos

# --- Full HTML Extractor Logic ---
def get_html_extraction_patterns():
    # RELAXED PATTERNS: Use .*? to ensure capture regardless of whitespace variations
    return [
        (r'<div[^>]*class=["\'][^"\']*highlight[^"\']*["\'][^>]*>.*?<pre[^>]*class=["\'][^"\']*(?:language-)?(\w+)[^"\']*["\'][^>]*><code[^>]*>(.*?)</code></pre>', "github-highlight"),
        (r'<div[^>]*class=["\'][^"\']*snippet-clipboard-content[^"\']*["\'][^>]*>.*?<pre[^>]*><code[^>]*>(.*?)</code></pre>', "github-snippet"),
        (r'<div[^>]*class=["\'][^"\']*codeBlockContainer[^"\']*["\'][^>]*>.*?<pre[^>]*class=["\'][^"\']*prism-code[^"\']*language-(\w+)[^"\']*["\'][^>]*>(.*?)</pre>', "docusaurus"),
        (r'<div[^>]*class=["\'][^"\']*language-(\w+)[^"\']*["\'][^>]*>.*?<pre[^>]*class=["\'][^"\']*prism-code[^"\']*language-(\w+)[^"\']*["\'][^>]*>(.*?)</pre>', "docusaurus-alt"),
        (r'<pre[^>]*><code[^>]*class=["\'][^"\']*language-(\w+)[^"\']*["\'][^>]*>(.*?)</code></pre>', "milkdown-typed"),
        (r'<div[^>]*class=["\'][^"\']*code-wrapper[^"\']*["\'][^>]*>.*?<pre[^>]*>(.*?)</pre>', "milkdown-wrapper"),
        (r'<div[^>]*class=["\'][^"\']*code-block-wrapper[^"\']*["\'][^>]*>.*?<pre[^>]*><code[^>]*>(.*?)</code></pre>', "milkdown-wrapper-code"),
        (r'<div[^>]*class=["\'][^"\']*milkdown-code-block[^"\']*["\'][^>]*>.*?<pre[^>]*><code[^>]*>(.*?)</code></pre>', "milkdown-code-block"),
        (r'<pre[^>]*class=["\'][^"\']*code-block[^"\']*["\'][^>]*><code[^>]*>(.*?)</code></pre>', "milkdown"),
        (r"<div[^>]*data-code-block[^>]*>.*?<pre[^>]*>(.*?)</pre>", "milkdown-alt"),
        (r'<div[^>]*class=["\'][^"\']*milkdown[^"\']*["\'][^>]*>.*?<pre[^>]*><code[^>]*>(.*?)</code></pre>', "milkdown-div"),
        (r'<div[^>]*class=["\'][^"\']*monaco-editor[^"\']*["\'][^>]*>.*?<div[^>]*class=["\'][^"\']*view-lines[^"\']*[^>]*>(.*?)</div>(?=.*?</div>.*?</div>)', "monaco"),
        (r'<div[^>]*class=["\'][^"\']*cm-content[^"\']*["\'][^>]*>((?:<div[^>]*class=["\'][^"\']*cm-line[^"\']*["\'][^>]*>.*?</div>\s*)+)</div>', "codemirror"),
        (r'<div[^>]*class=["\'][^"\']*CodeMirror[^"\']*["\'][^>]*>.*?<div[^>]*class=["\'][^"\']*CodeMirror-code[^"\']*["\'][^>]*>(.*?)</div>', "codemirror-legacy"),
        (r'<pre[^>]*class=["\'][^"\']*language-(\w+)[^"\']*["\'][^>]*>\s*<code[^>]*>(.*?)</code>\s*</pre>', "prism"),
        (r'<pre[^>]*>\s*<code[^>]*class=["\'][^"\']*language-(\w+)[^"\']*["\'][^>]*>(.*?)</code>\s*</pre>', "prism-alt"),
        (r'<pre[^>]*><code[^>]*class=["\'][^"\']*hljs(?:\s+language-(\w+))?[^"\']*["\'][^>]*>(.*?)</code></pre>', "hljs"),
        (r'<pre[^>]*class=["\'][^"\']*hljs[^"\']*["\'][^>]*><code[^>]*>(.*?)</code></pre>', "hljs-pre"),
        (r'<pre[^>]*class=["\'][^"\']*shiki[^"\']*["\'][^>]*(?:.*?style=["\'][^"\']*background-color[^"\']*["\'])?[^>]*>\s*<code[^>]*>(.*?)</code>\s*</pre>', "shiki"),
        (r'<pre[^>]*class=["\'][^"\']*astro-code[^"\']*["\'][^>]*>(.*?)</pre>', "astro-shiki"),
        (r'<div[^>]*class=["\'][^"\']*astro-code[^"\']*["\'][^>]*>.*?<pre[^>]*>(.*?)</pre>', "astro-wrapper"),
        (r'<div[^>]*class=["\'][^"\']*language-(\w+)[^"\']*["\'][^>]*>.*?<pre[^>]*>(.*?)</pre>', "vitepress"),
        (r'<div[^>]*class=["\'][^"\']*vp-code[^"\']*["\'][^>]*>.*?<pre[^>]*>(.*?)</pre>', "vitepress-vp"),
        (r"<div[^>]*data-nextra-code[^>]*>.*?<pre[^>]*>(.*?)</pre>", "nextra"),
        (r'<pre[^>]*class=["\'][^"\']*nx-[^"\']*["\'][^>]*><code[^>]*>(.*?)</code></pre>', "nextra-nx"),
        (r'<pre[^>]*><code[^>]*class=["\'][^"\']*language-(\w+)[^"\']*["\'][^>]*>(.*?)</code></pre>', "standard-lang"),
        (r"<pre[^>]*>.*?<code[^>]*>(.*?)</code>.*?</pre>", "standard"),
        (r'<div[^>]*class=["\'][^"\']*code-block[^"\']*["\'][^>]*>.*?<pre[^>]*>(.*?)</pre>', "generic-div"),
        (r'<div[^>]*class=["\'][^"\']*codeblock[^"\']*["\'][^>]*>(.*?)</div>', "generic-codeblock"),
        (r'<div[^>]*class=["\'][^"\']*highlight[^"\']*["\'][^>]*>.*?<pre[^>]*>(.*?)</pre>', "highlight")
    ]

# --- Full Text Extractor Logic ---
def get_text_extraction_patterns():
    return {
        "backtick": r"```(\w*)[^\n]*\n(.*?)```",
        "language_label": r"(?:^|\n)((?:typescript|javascript|python|java|c\+\+|rust|go|ruby|php|swift|kotlin|scala|r|matlab|julia|dart|elixir|erlang|haskell|clojure|lua|perl|shell|bash|sql|html|css|xml|json|yaml|toml|ini|dockerfile|makefile|cmake|gradle|maven|npm|yarn|pip|cargo|gem|pod|composer|nuget|apt|yum|brew|choco|snap|flatpak|appimage|msi|exe|dmg|pkg|deb|rpm|tar|zip|7z|rar|gz|bz2|xz|zst|lz4|lzo|lzma|lzip|lzop|compress|uncompress|gzip|gunzip|bzip2|bunzip2|xz|unxz|zstd|unzstd|lz4|unlz4|lzo|unlzo|lzma|unlzma|lzip|lunzip|lzop|unlzop)\s*(?:code|example|snippet)?)[:\s]*\n((?:(?:^[ \t]+.*\n?)+)|(?:.*\n)+?)(?=\n(?:[A-Z][a-z]+\s*:|^\s*$|\n#|\n\*|\n-|\n\d+\.))"
    }

import json
import re
from typing import Any, cast


def _extract_reasoning_strings(value: Any) -> list[str]:
    """Convert reasoning payload fragments into plain-text strings."""
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list | tuple | set):
        collected = []
        for item in value:
            collected.extend(_extract_reasoning_strings(item))
        return collected
    if isinstance(value, dict):
        candidates = []
        for key in ("text", "summary", "content", "message", "value", "parts"):
            if value.get(key):
                candidates.extend(_extract_reasoning_strings(value[key]))
        return candidates
    for attr in ("text", "summary", "content", "value"):
        if hasattr(value, attr):
            attr_val = getattr(value, attr)
            if attr_val:
                return _extract_reasoning_strings(attr_val)
    return []


def extract_message_text(choice: Any) -> tuple[str, str, bool]:
    """Extract primary content and reasoning text from a chat completion choice."""
    if not choice:
        return "", "", False
    message = choice.get("message") if isinstance(choice, dict) else getattr(choice, "message", None)
    if not message:
        return "", "", False

    raw_content = message.get("content") if isinstance(message, dict) else getattr(message, "content", "")
    content_text = raw_content.strip() if isinstance(raw_content, str) else ""

    reasoning_fragments = []
    for attr in ("reasoning", "reasoning_details", "reasoning_content"):
        val = message.get(attr) if isinstance(message, dict) else getattr(message, attr, None)
        if val:
            reasoning_fragments.extend(_extract_reasoning_strings(val))

    reasoning_text = "\n".join(f for f in reasoning_fragments if f).strip()

    if content_text and not reasoning_text:
        # Heuristic reasoning detection
        indicators = ["okay, let's see", "let me think", "analyzing", "breaking this down", "step by step"]
        # PERFORMANCE: Extracted content_text.lower() outside generators to prevent O(N*M) repeated allocations
        content_lower = content_text.lower()
        if any(ind in content_lower for ind in indicators):
            reasoning_text = content_text
            extracted = extract_json_from_reasoning(content_text)
            if extracted:
                content_text = extracted
            else:
                content_text = ""

    if not content_text and reasoning_text:
        content_text = reasoning_text
    return content_text, reasoning_text, bool(reasoning_text)


def extract_json_from_reasoning(reasoning_text: str, context_code: str = "", language: str = "") -> str:
    """Extract JSON content from reasoning text, with synthesis fallback."""
    if not reasoning_text:
        return ""
    json_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    json_matches = re.findall(json_block_pattern, reasoning_text, re.DOTALL | re.IGNORECASE)
    for match in json_matches:
        try:
            json.loads(match.strip())
            return cast(str, match.strip())
        except Exception:
            continue

    json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
    json_matches = re.findall(json_pattern, reasoning_text, re.DOTALL)
    for match in json_matches:
        try:
            parsed = json.loads(match.strip())
            if isinstance(parsed, dict) and any(key in parsed for key in ["example_name", "summary", "name", "title"]):
                return cast(str, match.strip())
        except Exception:
            continue
    return synthesize_json_from_reasoning(reasoning_text, context_code, language)


def synthesize_json_from_reasoning(reasoning_text: str, context_code: str = "", language: str = "") -> str:
    """Full-scale original synthesis logic with 15+ action patterns and 19+ tech patterns."""
    if not reasoning_text and not context_code:
        return ""
    text_lower = reasoning_text.lower() if reasoning_text else ""
    code_lower = context_code.lower() if context_code else ""
    combined = f"{text_lower} {code_lower}"

    action_patterns = [
        (r"\b(?:parse|parsing|parsed)\b", "Parse"),
        (r"\b(?:create|creating|created)\b", "Create"),
        (r"\b(?:analyze|analyzing|analyzed)\b", "Analyze"),
        (r"\b(?:extract|extracting|extracted)\b", "Extract"),
        (r"\b(?:generate|generating|generated)\b", "Generate"),
        (r"\b(?:process|processing|processed)\b", "Process"),
        (r"\b(?:load|loading|loaded)\b", "Load"),
        (r"\b(?:handle|handling|handled)\b", "Handle"),
        (r"\b(?:manage|managing|managed)\b", "Manage"),
        (r"\b(?:build|building|built)\b", "Build"),
        (r"\b(?:define|defining|defined)\b", "Define"),
        (r"\b(?:implement|implementing|implemented)\b", "Implement"),
        (r"\b(?:fetch|fetching|fetched)\b", "Fetch"),
        (r"\b(?:connect|connecting|connected)\b", "Connect"),
        (r"\b(?:validate|validating|validated)\b", "Validate"),
    ]
    tech_patterns = [
        (r"\bjson\b", "JSON"),
        (r"\bapi\b", "API"),
        (r"\bfile\b", "File"),
        (r"\bdata\b", "Data"),
        (r"\bcode\b", "Code"),
        (r"\btext\b", "Text"),
        (r"\bcontent\b", "Content"),
        (r"\bresponse\b", "Response"),
        (r"\brequest\b", "Request"),
        (r"\bconfig\b", "Config"),
        (r"\bllm\b", "LLM"),
        (r"\bmodel\b", "Model"),
        (r"\bexample\b", "Example"),
        (r"\bcontext\b", "Context"),
        (r"\basync\b", "Async"),
        (r"\bfunction\b", "Function"),
        (r"\bclass\b", "Class"),
        (r"\bprint\b", "Output"),
        (r"\breturn\b", "Return"),
    ]

    detected_actions = [a for p, a in action_patterns if re.search(p, combined)]
    detected_techs = [t for p, t in tech_patterns if re.search(p, combined)]

    if detected_actions and detected_techs:
        name = f"{detected_actions[0]} {detected_techs[0]}"
    elif detected_actions:
        name = f"{detected_actions[0]} Code"
    elif detected_techs:
        name = f"Handle {detected_techs[0]}"
    else:
        name = "Code Processing"

    words = name.split()
    if len(words) > 4:
        name = " ".join(words[:4])

    # Restored multi-line loops with proper variable names (Fixed E741)
    lines = []
    for raw_line in reasoning_text.split("\n"):
        if len(raw_line.strip()) > 10:
            lines.append(raw_line.strip())

    if lines:
        first = lines[0][:100] + "..." if len(lines[0]) > 100 else lines[0]
        action_name = detected_actions[0].lower() if detected_actions else "processing"
        summary = f"Code example showing {action_name} operations. {first}"
    else:
        summary = f"Code example demonstrating {name.lower()} functionality."

    if len(summary) > 300:
        summary = summary[:297] + "..."

    return json.dumps({"example_name": name, "summary": summary})

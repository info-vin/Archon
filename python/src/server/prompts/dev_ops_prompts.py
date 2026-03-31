"""
Prompts for DevBot and DevOps / Engineering Persona Prompts
"""

from ..schemas.tool_schemas import GenerateLogoArgs, RagSearchArgs, SearchCodeArgs


def get_devbot_analysis_prompt(command: str, stderr: str) -> str:
    """
    Returns the system prompt for DevBot L2 error analysis.
    """
    return f"""
You are an expert software engineer and debugger (Archon DevBot).
The following shell command failed:

Command: `{command}`

Error Output (stderr):
{stderr}

### YOUR MISSION
Analyze the error. You have access to MCP tools to search the codebase and knowledge base if needed.
1. If the error is a fixable code error (e.g., SyntaxError, logic bug, missing import), provide a fix.
2. If you are unsure about the correct implementation or API usage, use the `search_code_examples` tool BEFORE proposing a fix.

### RESPONSE FORMAT
You MUST return a JSON object with the following structure:
{{
    "file_path": "The relative path of the file to fix (e.g., 'scripts/foo.py')",
    "fixed_content": "The COMPLETE content of the fixed file (do not use diffs)",
    "reasoning": "A brief explanation of the fix and what tools you used to verify."
}}

If the error is an environment issue or you cannot fix it by modifying code, return an empty JSON object {{}}.
Ensure the "fixed_content" is valid code for the target language.
"""


# Tool definitions for OpenAI/Gemini Tool Calling

# Dynamic Tool Definitions using Pydantic
DEVBOT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_code_examples",
            "description": "Search the codebase for specific patterns or API usage examples.",
            "parameters": SearchCodeArgs.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rag_search_knowledge_base",
            "description": "Search the official documentation and knowledge base for help.",
            "parameters": RagSearchArgs.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_logo",
            "description": "Generate an SVG logo based on descriptive keywords.",
            "parameters": GenerateLogoArgs.model_json_schema(),
        },
    },
]

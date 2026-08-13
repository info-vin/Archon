"""
Prompts for scheduled patrol and automated tasks.
"""

SYS_ERROR_PATROL_PROMPT = (
    "Clockwork detected the following errors in the last hour:\n{error_summary}\n\nPlease analyze and fix."
)

LEADS_PATROL_PROMPT = (
    "Please write an engaging 600-word daily blog post summarizing today's tech job market movements.\n\n"
    "Data points ({lead_count} leads):\n{lead_summary}\n\n"
    "Focus on industry trends and written in Traditional Chinese (繁體中文)."
)

API_DEPRECATION_SCAN_PROMPT = (
    "Clockwork has initiated the bi-weekly scan of Google's Gemini API documentation.\n\n"
    "Please use your RAG and Web capabilities to extract the latest information regarding:\n"
    "1. Deprecated models and their sunset dates\n"
    "2. New model releases\n"
    "3. Quota changes\n\n"
    "Output a concise summary."
)

TECH_DEBT_CLEANUP_PROMPT = (
    "Clockwork detected the following technical debt that needs archiving or cleanup:\n\n"
    "{warnings_str}"
)

TECH_DEBT_SSOT_AUDIT_PROMPT = (
    "Clockwork detected the following hardcoded values (Network/Models/Prompts) that violate SSOT rules:\n\n"
    "{warnings_str}"
)

SOURCE_METADATA_SUMMARY = "You are a helpful assistant that provides concise library/tool/framework summaries."

SOURCE_TITLE_GENERATOR = "You are a helpful assistant that generates concise titles."

CODE_EXAMPES_AUDITOR = "You are a helpful assistant that analyzes code examples."

PROJECT_OWNER_ASSISTANT_PO = "You are POBot, a helpful Product Owner assistant. ALWAYS answer in Traditional Chinese (Taiwan繁體中文)."

CHARLIE_ASSISTANT_PM = "You are Charlie's Assistant. Answer in Traditional Chinese (Taiwan)."

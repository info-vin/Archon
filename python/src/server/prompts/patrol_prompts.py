"""
Prompts for scheduled patrol and automated tasks.
"""

SYS_ERROR_PATROL_PROMPT = (
    "Clockwork detected the following errors in the last hour:\n{error_summary}\n\nPlease analyze and fix."
)

LEADS_PATROL_PROMPT = (
    "Please write an engaging 800-word daily blog post summarizing today's tech job market movements.\n\n"
    "Data points ({lead_count} leads):\n{lead_summary}\n\n"
    "Please strictly follow these requirements:\n"
    "1. Language: Written in Traditional Chinese (繁體中文) for Taiwan market.\n"
    "2. Structure: \n"
    "   - Catchy Title: Create a high-converting, attention-grabbing title suitable for social media (e.g., using emojis, highlighting unusual or surprising industry combinations like medical or fragrance with AI).\n"
    "   - Introduction: Set the market trend context. Explain *why* traditional industries are racing to adopt AI today.\n"
    "   - Body Paragraphs: Focus on industry trends. Group relevant companies together. For each group, don't just list names—provide 1-2 sentences explaining the underlying business pain point or why this move is significant.\n"
    "   - Career Advice: Provide concrete, actionable insights for job seekers based on today's data (e.g., matching specific backgrounds like Python or Pre-sales to the open roles).\n"
    "   - Conclusion & CTA: End with a strong, interactive Call-to-Action. Explicitly invite readers to comment below with their thoughts or directly DM their resumes for a professional review.\n"
    "3. Persona Consistency: Use the single author persona name \"Archon\" consistently throughout the entire post. (e.g., \"大家好，我是 Archon！\" in the beginning and \"歡迎私訊聯繫 Archon\" in the conclusion). Do NOT switch or mix persona names (e.g., do not use Bob).\n"
    "4. Tone: Energetic, insightful, empathetic, and professional."
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

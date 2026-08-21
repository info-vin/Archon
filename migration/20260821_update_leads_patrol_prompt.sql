-- Update LEADS_PATROL_PROMPT for Daily Market Intelligence
UPDATE archon_prompts
SET prompt = 'Please write an engaging 800-word daily blog post summarizing today''s tech job market movements.

Data points ({lead_count} leads):
{lead_summary}

Please strictly follow these requirements:
1. Language: Written in Traditional Chinese (繁體中文) for Taiwan market.
2. Structure: 
   - Catchy Title: Create a high-converting, attention-grabbing title suitable for social media (e.g., using emojis, highlighting unusual or surprising industry combinations like medical or fragrance with AI).
   - Introduction: Set the market trend context. Explain *why* traditional industries are racing to adopt AI today.
   - Body Paragraphs: Focus on industry trends. Group relevant companies together. For each group, don''t just list names—provide 1-2 sentences explaining the underlying business pain point or why this move is significant.
   - Career Advice: Provide concrete, actionable insights for job seekers based on today''s data (e.g., matching specific backgrounds like Python or Pre-sales to the open roles).
   - Conclusion & CTA: End with a strong, interactive Call-to-Action. Explicitly invite readers to comment below with their thoughts or directly DM their resumes for a professional review.
3. Persona Consistency: Use the single author persona name "Archon" consistently throughout the entire post. (e.g., "大家好，我是 Archon！" in the beginning and "歡迎私訊聯繫 Archon" in the conclusion). Do NOT switch or mix persona names (e.g., do not use Bob).
4. Tone: Energetic, insightful, empathetic, and professional.',
    updated_at = NOW()
WHERE prompt_name = 'LEADS_PATROL_PROMPT';

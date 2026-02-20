-- migration/028_seed_voice_prompt.sql

-- Seed the voice transcription prompt into the system_prompts table
-- This allows Charlie/Admin to tune the extraction logic via UI.

INSERT INTO archon_prompts (prompt_name, prompt, description, created_at, updated_at)
VALUES (
    'VOICE_TRANSCRIPTION_PROMPT',
    '你是一位專業的業務助理。請準確地將這段銷售拜訪錄音轉錄為繁體中文逐字稿，並總結關鍵對話內容與提取具體後續任務清單。請嚴格以 JSON 格式回傳，包含鍵值：''transcript'', ''summary'', ''tasks'' (字串清單)。',
    'Used by the Visit Log API to process audio files via Gemini. Controls how voice notes are transcribed and what tasks are extracted.',
    NOW(),
    NOW()
)
ON CONFLICT (prompt_name) DO UPDATE SET
    prompt = EXCLUDED.prompt,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('028_seed_voice_prompt') ON CONFLICT (version) DO NOTHING;

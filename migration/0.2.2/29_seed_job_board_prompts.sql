-- Seed Job Board Prompts
INSERT INTO public.archon_prompts (prompt_name, prompt, description)
VALUES (
    'ALICE_INFER_NEED',
    'You are a sales assistant helping Alice (Sales Rep) analyze a job posting quickly on her mobile phone.
Job: {title} at {company}
Desc: {desc}

Output exactly 2 short markdown bullet points (max 50 words each) using Traditional Chinese (繁體中文):
- **技術棧**: [關鍵字與技術需求]
- **痛點預測**: [可能面臨的業務痛點與需求]',
    'Prompt for inferring customer needs from job descriptions in traditional Chinese.'
)
ON CONFLICT (prompt_name) DO UPDATE SET
    prompt = EXCLUDED.prompt,
    description = EXCLUDED.description;

-- Register migration version
INSERT INTO public.schema_migrations (version) 
VALUES ('29_seed_job_board_prompts') 
ON CONFLICT (version) DO NOTHING;

-- Phase 5.14: Update ALICE_LEAD_JUDGE prompt to structured A/B/C/X JSON classification
-- Idempotent update aligned with python/src/server/prompts/sales_prompts.py

UPDATE public.archon_prompts
SET prompt = $prompt$我們是一家 AI 自動化與 Agent 軟體顧問公司。核心能力：
{core_text}

請分析以下職缺：
Title: {title}
Desc: {desc}

請依下列 ICP 規則將該公司分類為 A、B、C、X 之一：
- A：30–300 人之傳統／非軟體企業、研究機構或醫院，缺乏內部 AI 團隊，有流程自動化或系統整合外包痛點。
- B：小型潛客（約 30 人以下），有明確 AI 導入或自動化需求（可轉介）。
- C：明確排除對象，包含同業 AI/LLM 軟體公司、SI 系統整合商、人力派遣、獵頭顧問、自動化設備商。
- X：與 AI／自動化／系統整合無關之職缺，或資訊不足無法判斷。

請僅輸出嚴格 JSON（不要加額外說明或 Markdown），格式如下：
{{"category": "A|B|C|X", "confidence": 0.0到1.0之間的數值, "reason": "繁體中文簡短判斷理由"}}$prompt$,
    updated_at = NOW()
WHERE prompt_name = 'ALICE_LEAD_JUDGE';

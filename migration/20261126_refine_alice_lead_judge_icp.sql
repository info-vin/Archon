-- Migration: 20261126_refine_alice_lead_judge_icp.sql
-- Purpose: Update ALICE_LEAD_JUDGE prompt in archon_prompts based on Phase 5.14 39-sample human calibration
--          (explicitly include traditional machinery/hardware/IC/media in A/B and strictly exclude ERP/IT SI peers in C).
-- Idempotent: Updates ALICE_LEAD_JUDGE and registers schema_migrations with ON CONFLICT DO NOTHING.

BEGIN;

UPDATE public.archon_prompts
SET prompt = $PROMPT$我們是一家 AI 自動化與 Agent 軟體顧問公司。核心能力：
{core_text}

請分析以下職缺：
Title: {title}
Desc: {desc}

請依下列 ICP 規則將該公司分類為 A、B、C、X 之一：
- A：30–300 人之傳統／非軟體企業（含傳統機械製造、工業電腦／硬體廠、研究機構或醫院），缺乏內部 AI 團隊，有流程自動化或系統整合外包痛點。
- B：小型潛客（約 30 人以下）或單一部門／媒體／IC 設計等非軟體同業之獨立專案，有明確 AI 導入、自動化或內部培訓需求（可轉介或小案切入）。
- C：明確排除對象：同業 AI/LLM 軟體顧問公司、接案型 SI／ERP 系統導入商（如資訊／智能科技幫客戶導入 ERP 者）、人力派遣、獵頭顧問、純自動化產線設備商。
- X：與 AI／自動化／系統整合無關之職缺，或資訊不足無法判斷。

請僅輸出嚴格 JSON（不要加額外說明或 Markdown），格式如下：
{{"category": "A|B|C|X", "confidence": 0.0到1.0之間的數值, "reason": "繁體中文簡短判斷理由"}}$PROMPT$,
    updated_at = NOW()
WHERE prompt_name = 'ALICE_LEAD_JUDGE';

INSERT INTO public.schema_migrations (version)
VALUES ('20261126_refine_alice_lead_judge_icp')
ON CONFLICT (version) DO NOTHING;

COMMIT;

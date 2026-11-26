# sales_prompts.py
# Used by MarketBot via marketing_api.py

SALES_PITCH_SYSTEM_PROMPT = """You are a top-tier Sales Representative for Archon, an AI & Data consultancy.
Your goal is to write a personalized, professional, and compelling email pitch to a hiring manager.
Structure: 1. Hook, 2. Value Prop (reference case study), 3. CTA.

OUTPUT FORMAT:
Please provide the output in two sections:
[ENGLISH PITCH]
(English version here)

[CHINESE PITCH]
(Chinese version here, culturally adapted for Taiwan market)
"""
"""
Default Prompt Templates (SSOT for Fallback Prompts)
"""

ALICE_HYDE_BASELINE_DEFAULT = (
    "請想像你是一家需要購買以下 AI 服務的傳統或非軟體公司，請寫出一篇 300 字的徵才職缺文案，尋找能幫你們導入這些技術的顧問或廠商。\n\n"
    "核心服務：\n{core_text}"
)

ALICE_LEAD_ICP_CRITERIA: dict[str, str] = {
    "A": "30–300 人之傳統／非軟體企業、研究機構或醫院，缺乏內部 AI 團隊，有流程自動化或系統整合外包痛點。",
    "B": "小型潛客（約 30 人以下），有明確 AI 導入或自動化需求（可轉介）。",
    "C": "明確排除對象，包含同業 AI/LLM 軟體公司、SI 系統整合商、人力派遣、獵頭顧問、自動化設備商。",
    "X": "與 AI／自動化／系統整合無關之職缺，或資訊不足無法判斷。",
}

ALICE_LEAD_JUDGE_DEFAULT = (
    "我們是一家 AI 自動化與 Agent 軟體顧問公司。核心能力：\n{core_text}\n\n"
    "請分析以下職缺：\nTitle: {title}\nDesc: {desc}\n\n"
    "請依下列 ICP 規則將該公司分類為 A、B、C、X 之一：\n"
    + "\n".join(f"- {k}：{v}" for k, v in ALICE_LEAD_ICP_CRITERIA.items())
    + "\n\n請僅輸出嚴格 JSON（不要加額外說明或 Markdown），格式如下：\n"
    '{{"category": "A|B|C|X", "confidence": 0.0到1.0之間的數值, "reason": "繁體中文簡短判斷理由"}}'
)

ALICE_INFER_NEED_DEFAULT = (
    "你是一位銷售助理。請用繁體中文列出該職缺的：\n"
    "- **技術棧**\n"
    "- **痛點預測**\n\n"
    "Job: {title} at {company}\n"
    "Desc: {desc}"
)

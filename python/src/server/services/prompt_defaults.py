"""
Default Prompt Templates (SSOT for Fallback Prompts)
"""

ALICE_HYDE_BASELINE_DEFAULT = (
    "請想像你是一家需要購買以下 AI 服務的傳統或非軟體公司，請寫出一篇 300 字的徵才職缺文案，尋找能幫你們導入這些技術的顧問或廠商。\n\n"
    "核心服務：\n{core_text}"
)

ALICE_LEAD_JUDGE_DEFAULT = (
    "我們是一家 AI 自動化與 Agent 軟體公司。我們的核心能力是：\n{core_text}\n\n"
    "請看以下職缺：\nTitle: {title}\nDesc: {desc}\n\n"
    "請問這家公司是：\n"
    "1. 我們的「潛在客戶」(他們缺乏 AI 能力，需要買我們的服務來自動化或導入 AI)。如果是，請回答 YES。\n"
    "2. 我們的「同業競爭者」(他們正在招募 AI 工程師，要自己開發 LLM 或 Agent)。如果是，請回答 NO。\n"
    "3. 完全無關。請回答 NO。\n\n"
    "只回答 YES 或 NO。"
)

ALICE_INFER_NEED_DEFAULT = (
    "你是一位銷售助理。請用繁體中文列出該職缺的：\n"
    "- **技術棧**\n"
    "- **痛點預測**\n\n"
    "Job: {title} at {company}\n"
    "Desc: {desc}"
)

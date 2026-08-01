# pm_prompts.py
# Used by POBot via task_service.py

USER_STORY_SYSTEM_PROMPT = """You are an expert Product Owner (PO) and Business Analyst.
Your goal is to refine vague task descriptions into structured User Stories with Acceptance Criteria.

Unless explicitly requested otherwise, always respond in Traditional Chinese (繁體中文).

You MUST use Markdown format.

Output Format:
# [Title]

## User Story
**As a** [role],
**I want to** [action],
**So that** [benefit].

## Acceptance Criteria
Please use Gherkin syntax (Given/When/Then) for at least one criteria if possible.
- [ ] **Scenario 1**:
  - Given [context]
  - When [action]
  - Then [expected result]
- [ ] **Scenario 2**:
  - ...

## Technical Notes
(Optional technical implementation details, e.g., API endpoints, database changes)
"""

REPORT_CONTEXT_DEFAULT = """### 系統運行上下文數據

**資料區間**：{end_date_str} 前推 {days} 天 (從 {start_date_str} 至 {end_date_str})
**報告產出日期**：{end_date_str}

#### 1. 商業開發線告 (Leads)
{leads_summary}

#### 2. AI 運算用量與成本 (Token Usage)
{token_summary}

#### 3. 系統警示與異常紀錄 (Archon Logs)
{logs_summary}

#### 4. 專案任務狀態異動 (Archon Tasks)
{tasks_summary}
"""

REPORT_CONTEXT_FALLBACK = "無法取得系統運行數據，請以無上下文模式進行總結。"

DAILY_EXECUTIVE_SUMMARY_DEFAULT = """昨日系統運行數據如下：

{context_md}

請啟動星環群聊，協調 Alice, Bob, DevBot 進行討論，最後由 Supervisor (Charlie) 彙整並提供每日執行摘要報告。
要求：
1. 所有的商業行銷數據、Token成本花費、系統警示數量，皆必須使用 Markdown 表格進行結構化對照，禁止純文字描述。
2. 在數據表格段落的上方，必須顯示並列出各項比率（如歸檔率、轉換率等）的計算來源與名詞定義（例如分子/分母公式），確保數據無歧義。"""

WEEKLY_EXECUTIVE_SUMMARY_DEFAULT = """這是過去 7 天的系統運行上下文數據：

{context_md}

請對每個專屬領域（Sales, Marketing, System, **Engineering/DevBot**）進行分析提煉，最後由 Supervisor 彙整並提供高知識品質、具體行動建議的執行摘要。
要求：
1. 所有的商業行銷數據、Token成本花費、系統警示數量，皆必須使用 Markdown 表格進行結構化對照，禁止純文字描述。
2. 在數據表格段落的上方，必須顯示並列出各項比率（如歸檔率、轉換率等）的計算來源與名詞定義（例如分子/分母公式），確保數據無歧義。"""

MONTHLY_EXECUTIVE_SUMMARY_DEFAULT = """這是過去 30 天的系統運行上下文數據：

{context_md}

請對每個專屬領域（Sales, Marketing, System, **Engineering/DevBot**）進行分析提煉，最後由 Supervisor 彙整並提供高知識品質、具體行動建議的執行摘要。
要求：
1. 所有的商業行銷數據、Token成本花費、系統警示數量，皆必須使用 Markdown 表格進行結構化對照，禁止純文字描述。
2. 在數據表格段落的上方，必須顯示並列出各項比率（如歸檔率、轉換率等）的計算來源與名詞定義（例如分子/分母公式），確保數據無歧義。"""

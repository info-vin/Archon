---
name: "Phase 4.2: Business Feature Expansion (HR & Market Intelligence) (繁體中文版)"
description: |
  This plan details the implementation of "Phase 6" from the original roadmap. 
  It focuses on delivering tangible business value through external integrations (Job Market Data) and internal analytics (HR Dashboard), transforming Archon from a pure development tool into a broader business intelligence assistant.
  (本計畫詳述了原路線圖中「Phase 6」的實作細節。重點在於透過外部整合（就業市場數據）與內部數據分析（HR 儀表板）來交付具體的商業價值，將 Archon 從單純的開發工具轉型為更廣泛的商業智慧助理。)

---

## Goal (目標)

**Feature Goal (功能目標)**: To expand Archon's capabilities beyond code generation into business operations, specifically by integrating real-time market data for recruiting and visualizing internal team performance. (將 Archon 的能力從代碼生成擴展至商業運營，具體而言，是透過整合即時的市場招聘數據以及視覺化內部團隊的績效表現。)

**Deliverable (交付成果)**: 
1.  **Marketing Intelligence Module (市場情報模組)**: A workflow to fetch job market data (e.g., 104 Job Bank) and generate market-aligned job descriptions. (一個用來獲取就業市場數據（如 104 人力銀行）並生成符合市場需求的職位描述的工作流。)
2.  **HR Analytics Dashboard (HR 分析儀表板)**: A visualization page displaying task distribution and team velocity metrics using charts. (一個使用圖表來顯示任務分佈與團隊速度指標的視覺化頁面。)

**Success Definition (成功定義)**: 
- A user can input a job title, retrieve valid market skills/keywords, and generate a draft JD. (使用者輸入職稱後，能檢索到有效的市場技能關鍵字，並生成職位描述草稿。)
- A manager can view a "Tasks by Status" pie chart and "Member Performance" bar chart populated with real database data. (管理者能看到由真實資料庫數據填充的「任務狀態分佈」圓餅圖與「成員績效」長條圖。)

## All Needed Context (所有需要的上下文)

### Documentation & References (文件與參考資料)

```yaml
- file: PRPs/Phase_4.1_AI_Developer_Implementation_Plan.md
  why: The parent roadmap that defined the architectural foundation for agents and RBAC. (定義了 Agent 與 RBAC 架構基礎的父計畫。)
- file: api-uml-diagrams.md
  why: Reference for defining new API endpoints consistent with existing patterns. (用於定義與現有模式一致的新 API 端點的參考。)
- url: https://github.com/it-jia/job104_spider
  why: Technical reference for reverse-engineering 104 Job Bank's internal AJAX API and headers. (用於逆向分析 104 內部 AJAX API 與 Headers 的技術參考。)
```

### Proposed Codebase Changes (預計變更的檔案結構)

```bash
python/
├── src/
│   ├── server/
│   │   ├── api_routes/
│   │   │   └── stats_api.py        # ADDED: Endpoints for HR analytics (aggregation queries). (新增：HR 分析的端點，處理聚合查詢)
│   │   └── services/
│   │       └── job_board_service.py # ADDED: Service to handle external job board AJAX simulation. (新增：處理外部求職網 AJAX 模擬的服務)
│   └── mcp_server/
│       └── features/
│           └── marketing/          # ADDED: New feature category. (新增：新的功能類別)
│               └── job_tools.py    # ADDED: MCP Tool exposing job search to the Agent. (新增：將職缺搜尋功能暴露給 Agent 的 MCP 工具)
enduser-ui-fe/
├── src/
│   ├── pages/
│   │   ├── MarketingPage.tsx       # ADDED: UI for Job Description generation workflow. (新增：職位描述生成工作流的 UI)
│   │   └── StatsPage.tsx           # ADDED: UI for HR Dashboard. (新增：HR 儀表板的 UI)
│   ├── components/
│   │   └── charts/                 # ADDED: Reusable chart components. (新增：可重複使用的圖表元件)
│   │       ├── TaskDistributionChart.tsx
│   │       └── LeaderboardChart.tsx
│   └── services/
│       └── api.ts                  # MODIFIED: Added client methods for stats and job search. (修改：新增用於統計與職缺搜尋的客戶端方法)
├── package.json                    # MODIFIED: Add `recharts` dependency. (修改：新增 `recharts` 依賴)
```

### Tech Stack Note (技術堆疊註記)
- **Backend HTTP Client**: Use `httpx` (Async) instead of `requests` to prevent blocking the FastAPI event loop during external API calls. (後端 HTTP 客戶端：使用 `httpx` (非同步) 取代 `requests`，以防止在呼叫外部 API 時阻塞 FastAPI 事件迴圈。)


## Implementation Blueprint (實作藍圖)

### Phase 1: HR Analytics Dashboard (Internal Data) (HR 分析儀表板 - 內部數據)
*Focus: Visualize existing data in `archon_tasks` to provide management insights. (重點：視覺化 `archon_tasks` 中的現有數據以提供管理洞察。)*

```yaml
Task 1: INFRA - Install Visualization Library (基礎建設 - 安裝視覺化函式庫)
  - [x] FILE: `enduser-ui-fe/package.json`
  - [x] ACTION: Add `recharts` to dependencies. (將 `recharts` 加入依賴)
  - [x] COMMAND: `cd enduser-ui-fe && pnpm install recharts`

Task 2: BACKEND - Create Statistics API (後端 - 建立統計 API)
  - [x] FILE: `python/src/server/api_routes/stats_api.py`
  - [x] ACTION: Define `APIRouter` with prefix `/api/stats`. (定義前綴為 `/api/stats` 的 `APIRouter`)
  - [x] ENDPOINT: `GET /tasks-by-status`
    - [x] LOGIC: SQL `SELECT status, COUNT(*) FROM archon_tasks GROUP BY status`.
    - [x] RESPONSE: List of `{ name: string, value: number }`.
  - [x] ENDPOINT: `GET /member-performance`
    - [x] LOGIC: SQL `SELECT assignee, COUNT(*) FROM archon_tasks WHERE status='done' GROUP BY assignee ORDER BY count DESC LIMIT 10`.
    - [x] RESPONSE: List of `{ name: string, completed_tasks: number }`.
  - [x] FILE: `python/src/server/main.py`
    - [x] ACTION: Include `stats_api.router`.

Task 3: FRONTEND - Integrate Stats API (前端 - 整合統計 API)
  - [x] FILE: `enduser-ui-fe/src/services/api.ts`
  - [x] ACTION: Add methods `getTaskDistribution()` and `getMemberPerformance()`. (新增 `getTaskDistribution()` 與 `getMemberPerformance()` 方法)

Task 4: FRONTEND - Implement Chart Components (前端 - 實作圖表元件)
  - [x] FILE: `enduser-ui-fe/src/pages/StatsPage.tsx`
  - [x] ACTION: Create a layout using `recharts` (PieChart for status, BarChart for performance). (使用 `recharts` 建立佈局：狀態圓餅圖、績效長條圖)
  - [x] ACTION: Implement loading states and error handling if data is empty. (實作載入狀態以及數據為空時的錯誤處理)
  - [x] ROUTING: Add `/stats` route in `App.tsx` and sidebar link. (在 `App.tsx` 新增 `/stats` 路由與側邊欄連結)
```

### Phase 2: Job Market Integration (External Data) (就業市場整合 - 外部數據)
*Focus: Enable the Agent to access external world data to assist in content creation. (重點：使 Agent 能夠存取外部世界數據以協助內容創作。)*

```yaml
Task 1: BACKEND - Job Board Service (後端 - 求職網服務)
  - [x] FILE: `python/src/server/services/job_board_service.py`
  - [x] ACTION: Create class `JobBoardService`.
  - [x] TECHNICAL REFERENCE (技術參考):
      - **Inspiration**: Reference patterns from `job104_spider` (GitHub). (參考 GitHub 上的 `job104_spider` 模式。)
      - **Target**: Simulate the internal 104 AJAX search API (`/jobs/search/list`) instead of HTML scraping. (目標：模擬 104 內部 AJAX 搜尋 API 而非直接進行 HTML 爬取。)
      - **Key Requirements**: Must include mandatory headers (`Referer`, `User-Agent`) identified in recent open-source research. (關鍵需求：必須包含在近期開源研究中識別出的必要 Headers。)
  - [x] IMPLEMENTATION STEPS:
      - 1. **Probing**: Test the endpoint with `requests` to verify if 104 has added new anti-bot signatures (e.g., `_sig` parameters). (測試端點以驗證 104 是否新增了簽名驗證。)
      - 2. **Service Logic**: Map the returned JSON fields (`jobName`, `description`, `jobDescription`) to our internal `JobData` schema. (將回傳的 JSON 欄位映射至內部的 `JobData` 架構。)
      - 3. **Fallback**: If the API is blocked by dynamic signature logic, use **Structured Mock Data** to prevent blocking Phase 2. (若 API 被動態簽名邏輯攔截，則降級為模擬數據以避免阻塞 Phase 2。)

Task 2: MCP - Expose Tool to Agent (MCP - 暴露工具給 Agent)
  - [x] FILE: `python/src/mcp_server/features/marketing/job_tools.py`
  - [x] ACTION: Create `SearchJobMarketTool` utilizing `JobBoardService`. (建立使用 `JobBoardService` 的 `SearchJobMarketTool`。)
  - [x] PROMPT: "Use this tool to find current market requirements for a specific job title." (提示詞：「使用此工具查找特定職稱的當前市場需求。」)

Task 3: FRONTEND - Marketing Workflow UI (前端 - 行銷工作流介面)
  - [x] FILE: `enduser-ui-fe/src/pages/MarketingPage.tsx`
  - [x] ACTION: Create a simple form: Input "Job Title" -> Button "Analyze Market" -> Display "Key Skills Found" -> Button "Generate JD". (建立簡易表單：輸入「職稱」-> 按鈕「分析市場」-> 顯示「關鍵技能」-> 按鈕「生成 JD」。)
  - [x] ROUTING: Add `/marketing` route in `App.tsx`. (在 `App.tsx` 新增 `/marketing` 路由。)
```

## Validation Loop (驗證迴圈)

### Level 1: Backend Unit Tests (後端單元測試)
- [x] ACTION: Create `python/tests/server/api_routes/test_stats_api.py`.
- [x] ASSERT: `GET /tasks-by-status` returns correct counts for seeded mock data. (斷言：`GET /tasks-by-status` 回傳正確的 Mock 種子數據計數。)
- [x] ASSERT: `GET /member-performance` correctly sorts users by completed tasks. (斷言：`GET /member-performance` 正確依完成任務數排序使用者。)

### Level 2: Manual Feature Verification (手動功能驗證)
- [x] ACTION: Navigate to `/stats`.
- [x] VERIFY: Charts render correctly without crashing on empty data. (驗證：圖表正確渲染，且在無數據時不會崩潰。)
- [x] ACTION: Navigate to `/marketing`.
- [x] VERIFY: Job search returns results (even if mocked initially) and UI displays them. (驗證：職缺搜尋回傳結果（即使初期是 Mock 的）且 UI 正確顯示。)

## Final Validation Checklist (最終驗證清單)

- [x] `make test-be` passes with new stats tests. (通過包含新統計測試的 `make test-be`)
- [x] Frontend builds successfully (`pnpm build`) with `recharts`. (前端包含 `recharts` 成功建置)
- [x] No mixed content warnings when fetching external data (if applicable). (抓取外部數據時無混合內容警告)

## Additional Notes (補充說明)
- **Tech Stack Updates**:
    - **Backend**: Updated `uv` dependencies to include `requests` (for testing probe) and verified `httpx` usage in production code.
    - **Environment**: Verified `.env` loading in tests.
- **Testing Strategy**:
    - **E2E**: No automated E2E tests for charts/external API (Visual/Manual verification only). (無自動化 E2E 測試，依賴視覺與手動驗證。)
    - **Regression**: Fixed `AgentService` tests that were failing due to logging changes.

### 補充：情境釐清與技術缺口 (Refinement on Scenario & Technical Gaps)

1.  **情境比對與修正 (Scenario Alignment)**:
    *   **Phase 4.0 提案**: 原本設想為「行銷練習場景」，重點在於文案撰寫練習。
    *   **Phase 4.2 現況**: 原本流程設計為「生成 JD」，這偏向 HR 招募功能，與「行銷」分類有語意衝突。
    *   **修正後情境 (Sales Intelligence)**:
        *   **角色**: B2B 業務/行銷人員。
        *   **流程**: 搜尋特定職缺 (如「商業分析師」) -> 找出正在招募該職位的公司 -> 識別潛在客戶 (Leads)。
        *   **價值**: 透過職缺需求反推公司的軟體/服務採購需求 (例如：招募數據分析師的公司可能需要 BI 工具)。
        *   **調整**: 產出結果不應僅是 JD，而應包含「潛在客戶列表」或「業務開發切入點分析」。

2.  **技術與流程缺口 (Technical Gaps)**:
    *   **端對端驗證 (E2E Verification)**: 目前專案缺乏針對「前端 -> 後端 -> 外部 API」的自動化 E2E 測試。引入外部數據源 (104) 後，此驗證機制的薄弱將成為穩定性風險。
    *   **資料庫 schema 討論 (Supabase SQL)**: 若要落實上述「潛在客戶」情境，目前的 `archon_tasks` 表不足以支撐。需要規劃新的資料表 (如 `leads`, `market_insights`) 來儲存搜尋結果與分析數據，這部分需要整體的 SQL 架構討論。
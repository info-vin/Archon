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
```

### Proposed Codebase Changes (預計變更的檔案結構)

```bash
python/
├── src/
│   ├── server/
│   │   ├── api_routes/
│   │   │   └── stats_api.py        # ADDED: Endpoints for HR analytics (aggregation queries). (新增：HR 分析的端點，處理聚合查詢)
│   │   └── services/
│   │       └── job_board_service.py # ADDED: Service to handle external job board fetching/scraping. (新增：處理外部求職網數據抓取/爬蟲的服務)
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

## Implementation Blueprint (實作藍圖)

### Phase 1: HR Analytics Dashboard (Internal Data) (HR 分析儀表板 - 內部數據)
*Focus: Visualize existing data in `archon_tasks` to provide management insights. (重點：視覺化 `archon_tasks` 中的現有數據以提供管理洞察。)*

```yaml
Task 1: INFRA - Install Visualization Library (基礎建設 - 安裝視覺化函式庫)
  - [ ] FILE: `enduser-ui-fe/package.json`
  - [ ] ACTION: Add `recharts` to dependencies. (將 `recharts` 加入依賴)
  - [ ] COMMAND: `cd enduser-ui-fe && pnpm install recharts`

Task 2: BACKEND - Create Statistics API (後端 - 建立統計 API)
  - [ ] FILE: `python/src/server/api_routes/stats_api.py`
  - [ ] ACTION: Define `APIRouter` with prefix `/api/stats`. (定義前綴為 `/api/stats` 的 `APIRouter`)
  - [ ] ENDPOINT: `GET /tasks-by-status`
    - [ ] LOGIC: SQL `SELECT status, COUNT(*) FROM archon_tasks GROUP BY status`.
    - [ ] RESPONSE: List of `{ name: string, value: number }`.
  - [ ] ENDPOINT: `GET /member-performance`
    - [ ] LOGIC: SQL `SELECT assignee, COUNT(*) FROM archon_tasks WHERE status='done' GROUP BY assignee ORDER BY count DESC LIMIT 10`.
    - [ ] RESPONSE: List of `{ name: string, completed_tasks: number }`.
  - [ ] FILE: `python/src/server/main.py`
    - [ ] ACTION: Include `stats_api.router`.

Task 3: FRONTEND - Integrate Stats API (前端 - 整合統計 API)
  - [ ] FILE: `enduser-ui-fe/src/services/api.ts`
  - [ ] ACTION: Add methods `getTaskDistribution()` and `getMemberPerformance()`. (新增 `getTaskDistribution()` 與 `getMemberPerformance()` 方法)

Task 4: FRONTEND - Implement Chart Components (前端 - 實作圖表元件)
  - [ ] FILE: `enduser-ui-fe/src/pages/StatsPage.tsx`
  - [ ] ACTION: Create a layout using `recharts` (PieChart for status, BarChart for performance). (使用 `recharts` 建立佈局：狀態圓餅圖、績效長條圖)
  - [ ] ACTION: Implement loading states and error handling if data is empty. (實作載入狀態以及數據為空時的錯誤處理)
  - [ ] ROUTING: Add `/stats` route in `App.tsx` and sidebar link. (在 `App.tsx` 新增 `/stats` 路由與側邊欄連結)
```

### Phase 2: Job Market Integration (External Data) (就業市場整合 - 外部數據)
*Focus: Enable the Agent to access external world data to assist in content creation. (重點：使 Agent 能夠存取外部世界數據以協助內容創作。)*

```yaml
Task 1: BACKEND - Job Board Service (後端 - 求職網服務)
  - [ ] FILE: `python/src/server/services/job_board_service.py`
  - [ ] ACTION: Create class `JobBoardService`. (建立 `JobBoardService` 類別)
  - [ ] METHOD: `search_jobs(keyword: str) -> list[JobData]`
  - [ ] IMPLEMENTATION: 
      - Initially implement a structured mock or use a lightweight scraper (BeautifulSoup/Playwright) if 104 API is unavailable. (初期若 104 API 不可用，先實作結構化的 Mock 或使用輕量爬蟲 BeautifulSoup/Playwright。)
      - *Constraint*: Must handle network timeouts and rate limiting gracefully. (限制：必須優雅地處理網路超時與速率限制。)

Task 2: MCP - Expose Tool to Agent (MCP - 暴露工具給 Agent)
  - [ ] FILE: `python/src/mcp_server/features/marketing/job_tools.py`
  - [ ] ACTION: Create `SearchJobMarketTool` utilizing `JobBoardService`. (建立使用 `JobBoardService` 的 `SearchJobMarketTool`。)
  - [ ] PROMPT: "Use this tool to find current market requirements for a specific job title." (提示詞：「使用此工具查找特定職稱的當前市場需求。」)

Task 3: FRONTEND - Marketing Workflow UI (前端 - 行銷工作流介面)
  - [ ] FILE: `enduser-ui-fe/src/pages/MarketingPage.tsx`
  - [ ] ACTION: Create a simple form: Input "Job Title" -> Button "Analyze Market" -> Display "Key Skills Found" -> Button "Generate JD". (建立簡易表單：輸入「職稱」-> 按鈕「分析市場」-> 顯示「關鍵技能」-> 按鈕「生成 JD」。)
  - [ ] ROUTING: Add `/marketing` route in `App.tsx`. (在 `App.tsx` 新增 `/marketing` 路由。)
```

## Validation Loop (驗證迴圈)

### Level 1: Backend Unit Tests (後端單元測試)
- [ ] ACTION: Create `python/tests/server/api_routes/test_stats_api.py`.
- [ ] ASSERT: `GET /tasks-by-status` returns correct counts for seeded mock data. (斷言：`GET /tasks-by-status` 回傳正確的 Mock 種子數據計數。)
- [ ] ASSERT: `GET /member-performance` correctly sorts users by completed tasks. (斷言：`GET /member-performance` 正確依完成任務數排序使用者。)

### Level 2: Manual Feature Verification (手動功能驗證)
- [ ] ACTION: Navigate to `/stats`.
- [ ] VERIFY: Charts render correctly without crashing on empty data. (驗證：圖表正確渲染，且在無數據時不會崩潰。)
- [ ] ACTION: Navigate to `/marketing`.
- [ ] VERIFY: Job search returns results (even if mocked initially) and UI displays them. (驗證：職缺搜尋回傳結果（即使初期是 Mock 的）且 UI 正確顯示。)

## Final Validation Checklist (最終驗證清單)

- [ ] `make test-be` passes with new stats tests. (通過包含新統計測試的 `make test-be`)
- [ ] Frontend builds successfully (`pnpm build`) with `recharts`. (前端包含 `recharts` 成功建置)
- [ ] No mixed content warnings when fetching external data (if applicable). (抓取外部數據時無混合內容警告)
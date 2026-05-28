# Phase 5.4.5: 主動式網路混沌攔截與多租戶帳單硬化計畫

本計畫定義了在 Phase 5.4.4 資料庫與基礎設施優化完成後，後續針對「主動式網路混沌攔截」與「多租戶與帳單分析（AI 經濟治理）」兩大進階功能的實體硬化藍圖。

---

## 建議變更

### 第一部分：主動式網路混沌攔截 (Active Network Chaos Interception)

目前數位雙生模擬器 (`simulator_runner.py`) 中的混沌測試仍是透過隨機模擬來展現，尚未真正影響網路封包。本階段將透過 Playwright 的網絡攔截機制進行實體硬化。

1. **Playwright 網絡封包路由器整合**：
   - 在 `scripts/twin_scout.py` 的 `YAMLScenarioRunner` 中，導入 Playwright 的 `page.route` API，攔截前端向 API 伺服器發出的所有 HTTP 請求。
2. **YAML 混沌參數支援**：
   - 擴充 Scenario YAML 的 Schema，支援在腳本中宣告混沌規則：
     ```yaml
     chaos:
       latency_ms: 1500  # 模擬 1.5 秒延遲
       error_rate: 0.1   # 10% 機率回傳 HTTP 500
       offline_steps: [3, 5]  # 在第 3 與第 5 步模擬斷網
     ```
3. **驗證前端自癒能力**：
   - 藉由攔截使 API 回傳 500 或 Timeout，測試前端的「加載防禦機制」與「錯誤重試邏輯」是否確實運作，而不會引發 React 渲染崩潰或 UI 永久卡死。

---

### 第二部分：多租戶支援與部門帳單硬化 (Multi-tenant & Billing Hardening)

落實架構文件中的多租戶規劃，並將 Token 用量分析（AI 經濟治理）升級為租戶與部門計費模式。

1. **資料庫多租戶欄位擴充 (`tenant_id`)**：
   - 設計非破壞性遷移腳本，為核心業務資料表（如 `projects`、`tasks`、`sources`）補上 `tenant_id UUID` 欄位。
   - 更新 Supabase Row Level Security (RLS) 政策，綁定 `auth.jwt() -> 'tenant_id'` 宣告，強制進行物理級別的租戶隔離。
2. **Token 計費與預算管控硬化**：
   - 完善 `TokenUsageTable` 的後端彙整 API，依據 `TOKEN_PRICING_JSON` 設定計算出每個租戶、每個部門的累計預算消耗。
   - **預算熔斷機制 (Budget Breaker)**：當某租戶或部門的累計 Token 消耗金額超過設定的預算閾值時，API 攔截器將自動回傳 HTTP 402 (Payment Required)，暫時阻斷 AI 運算請求，防止雲端費用失控。

---

## 執行結果一：Playwright 混沌攔截與自癒驗證

- **實體改造**：
  - 修改 `scripts/twin_scout.py` 中的 `YAMLScenarioRunner`，在 Playwright 上下文初始化後調用 `ctx.route("**/api/**", ...)`。
  - 設計混沌攔截器（Chaos Handler）：隨機注入 `latency_ms`（人工延遲）與 500 伺服器錯誤（回傳 `{"error": "Internal Chaos Server Error"}`），並在指定的 `offline_steps` 步數自動斷網（Abort HTTP Request）。
  - 更新 `scripts/level_generator.py` 生成 Campaign B 參數化混沌關卡（共 30 關）。
- **實彈運行驗證**：
  - 執行指令：`uv run python ../scripts/simulator_runner.py --headless true --chaos true --limit 5`
  - 結果：**5/5 關卡全數 PASS (Success Rate: 100.0%)**。
  - 運行期間成功模擬出多起 HTTP 500 與 Latency 延遲，前端 API 客戶端優雅攔截，UI 成功進行加載防禦與重試，模擬器無任何崩潰。

---

## 執行結果二：多租戶隔離與 RLS 加固

- **資料庫遷移與 RLS 硬化**：
  - 設計並套用了 SQL 增量遷移檔 `migration/0.2.2/23_multi_tenant_and_rls_hardening.sql`：
    - 為 `profiles`、`archon_projects`、`archon_tasks`、`leads`、`token_usage` 添加 `tenant_id` 欄位，預設指向系統預留租戶 UUID `d3b07384-d113-4456-a111-c91823710000`。
    - 建立 `get_auth_tenant_id()` SECURITY DEFINER 函數安全獲取目前使用者的租戶，規避 RLS 政策引發的 SQL 無限遞迴。
    - 更新並啟用 RLS 政策，將所有查詢/修改與 `get_auth_tenant_id()` 物理綁定，保障租戶資料的物理防禦。

---

## 執行結果三：FastAPI 預算熔斷 (Budget Guard) 中間件與前端對接

- **預算熔斷機制 (Budget Breaker)**：
  - 新增後端中間件 `python/src/server/middleware/budget_guard.py` 並在 `python/src/server/main.py` 的 CORSMiddleware 後掛載。
  - 每個非 GET 之 API/LLM 請求進入前，均會在 `token_usage` 表查詢當前租戶累計的 API Token 金額。一旦超出 `BUDGET_LIMIT_USD`（預設為 10.0），則主動熔斷並回傳 `HTTP 402 Payment Required`。
- **前端攔截與霓虹警告 Badge**：
  - 修改 `archon-ui-main/src/features/shared/api/apiClient.ts` 攔截 `402` 狀態，並在 window 上 dispatch `archon-budget-exceeded` CustomEvent。
  - 在 `MainLayout.tsx` 註冊事件監聽，收到事件時彈出橙色霓虹警告 Toast（Warning Badge），引導使用者，保障 React 不崩潰且無全頁空白。

---

## 執行結果四：系統與單元測試驗證成果

1. **前後端強型別與靜態檢查**：
   - **`npx tsc --noEmit`** ➜ 0 type errors.
   - **`uv run ruff check` / `mypy`** ➜ All checks passed, 0 type errors.
2. **後端單元與整合測試 (`make test-be`)**：
   - **575 個測試全數 PASS** (6 skipped, 5 xfailed, 0 failed)，執行時間 126.64 秒，無任何迴歸錯誤。
3. **角色物理對帳煙霧測試 (`make persona-audit`)**：
   - 針對 5 大角色 (Alice, Bob, Charlie, David, Agents) 的 API 入口與權限控制進行實彈公證，**全數回傳 200 OK**，業務功能暢通。


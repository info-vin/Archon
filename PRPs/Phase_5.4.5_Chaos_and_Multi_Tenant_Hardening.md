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

## 驗證計畫

### 自動化驗證
- **混沌模擬驗證**：執行 `make twin-simulator --chaos true`，確認即使注入 10% 的 API 500 錯誤率，模擬器仍能自癒完成任務或產出正確的故障日誌。
- **多租戶隔離驗證**：編寫 Pytest 整合測試，模擬 A 租戶試圖透過 API 讀取 B 租戶的專案，驗證 Supabase RLS 是否能 100% 物理阻斷並回傳 403。

### 手動驗證
- 登入 Admin UI 查看 **AI 經濟治理看板**，確認各部門/租戶的 Token 消耗趨勢與預算條能正確按部門加載，且排版無溢位或閃爍現象。

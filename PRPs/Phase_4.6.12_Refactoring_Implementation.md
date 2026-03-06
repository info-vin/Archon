# Phase 4.6.12: 巨型模組物理拆分與邏輯解耦計畫 (Architectural Decomposition)

> **前言**: 基於 Phase 4.6.11 的掃描結果，本階段鎖定 8 個行數超過 1000 行的「重災區」檔案。目標是透過物理拆分將單一檔案行數降至 600 行以下，達成 L2 級別的模組化硬化。

---

## 1. 執行標的與量化指標

| 標的檔案 | 目前行數 | 目標行數 | 拆分策略 |
| :--- | :--- | :--- | :--- |
| `projects_api.py` | 1720 | < 600 | 垂直拆分為 Core, Ops, 與 Versioning |
| `code_extraction_service.py` | 1583 | < 500 | 抽離 AST 解析引擎與 Language Drivers |
| `ollama_api.py` | 1335 | < 500 | 拆分為 Model Management 與 Inference |
| `llm_provider_service.py` | 1278 | < 400 | 實施 Provider Factory Pattern |
| `useRagSettingsData.ts` | 1181 | < 400 | 拆分為 State, Validation, 與 Actions |
| `knowledge_api.py` | 1132 | < 500 | 拆分為 Search 與 Indexing 控制層 |
| `model_discovery_service.py` | 1122 | < 500 | 抽離 Scan 邏輯與 Cache 管理器 |
| `task_service.py` | 1003 | < 600 | 抽離 AI Dispatcher 與 Metrics 計算 |

---

## 2. 落地實作 SOP (Surgical Refactoring)

### 步驟 1: API 路由物理切割 (L2 Hardening)
1.  **建立目錄結構**：在 `api_routes/` 下建立與原檔案同名的資料夾（例如 `api_routes/projects/`）。
2.  **邏輯搬移**：將 `APIRouter` 的 Endpoint 按功能群組搬移至 `base.py`, `versioning.py`, `stats.py`。
3.  **掛載對齊**：在 `api_routes/projects/__init__.py` 中匯總 Router，確保 `main.py` 無需大幅改動。

### 步驟 2: Service 邏輯解耦 (Domain Separation)
1.  **識別純函數**：將不依賴 `self` 的邏輯移至 `utils/` 或 `logic/` 子目錄。
2.  **繼承優化**：利用 `BaseRepository` 提供的 `execute_query`，確保拆分後的 Service 依然保持標準化的回傳格式。
3.  **依賴注入**：使用構造函數注入（Constructor Injection）解決拆分後的相互依賴。

### 步驟 3: 前端 Hook 降維
1.  **功能聚合**：將相關的 `useMemo` 與 `useCallback` 封裝進子 Hook。
2.  **Context 優化**：若子 Hook 間需要共享狀態，使用獨立的 `Context` 或狀態提升，避免 `useRagSettingsData.ts` 成為全能上帝類。

---

## 3. 風險評估與驗證計畫 (Safety Plan)

### 三大失敗點預測：
1.  **Circular Import (後端)**：拆分 Service 時極易發生循環引用。
    *   *對策*：嚴格遵守 `repositories -> services -> api_routes` 的單向依賴路徑。
2.  **Broken Path (前端)**：Hook 拆分後，相對路徑引用可能失效。
    *   *對策*：全面使用 `@/` 別名，並在拆分後立即執行 `pnpm test`。
3.  **State Desync (連動失效)**：拆分 Hook 可能導致原本的 `useEffect` 連動失效。
    *   *對策*：建立單元測試覆蓋關鍵狀態轉換路徑。

### 驗證指令：
- **後端**：`make lint-be && make test-be`
- **前端 (3737)**：`cd archon-ui-main && pnpm test`
- **前端 (5173)**：`cd enduser-ui-fe && pnpm test:unit`

---

## 4. 結論 (Success Definition)
Phase 4.6.12 完成後，全系統應**不再存在任何行數超過 1000 行的原始碼檔案**，且後端測試通過率必須維持在 100% (550/550)。

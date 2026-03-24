# Phase 4.6.17: 系統同步與自動化落地 (System Synchronization & Realization)

## 🎯 核心目標
終結「樂觀路徑」導致的 Bug 循環，實現 5 個服務的物理健康與 6 個自動化任務的實體產出。

## 🔍 現狀診斷 (Physical Evidence)
1.  **服務斷層**：`archon-server` 因導入格式混亂不穩定；`archon-mcp` 遺失核心工具；`archon-agents` 無法取得密鑰。
2.  **任務斷層**：`LAST_RUN` 停留在 03:36 AM，Alice 被 104 攔截，Bob 因無資料而空轉且不更新時間戳記。
3.  **前端斷層**：5173 呼叫 Admin API 導致 403，缺少考勤路由導致 404，`.env` 不一致導致 400。

---

## 🛠 實施計畫 (Implementation Plan)

### 第一階段：基礎設施硬化 (Infrastructure Alignment)
- **[Task A1] 導入路徑標準化**：批量修正 `api_routes/` 下所有絕對路徑為相對路徑，徹底解決 GAP-031 導致的 403 報錯。
- **[Task A2] MCP 工具恢復**：修復 `archon-mcp` 的導入層級，確保 `Marketing tools` 與 `Developer tools` 正確掛載。
- **[Task A3] 內部 API 通訊修復**：修正 `/internal/credentials/agents` 的存取控制，讓 Agents 服務能恢復健康。
- **[Task A4] 全域環境同步**：在 `Makefile` 建立 `make sync-env` 指令，強制物理同步所有專案的 `.env`。

### 第二階段：自動化任務落地 (Automation Realization)
- **[Task B1] Alice 爬蟲升級**：更新 `job_board_service.py`，加入 `Referer` 與人機驗證繞過邏輯，確保抓到真實數據。
- **[Task B2] Scheduler 邏輯加固**：重構 `_update_last_run` 邏輯，確保 6 個任務無論執行結果如何，**必定**更新資料庫時間戳記。
- **[Task B3] 健康檢查修復**：修正 `HealthService.py` 中的類型比較 Bug，恢復 System Probe 巡邏。
- **[Task B4] Bob 邏輯對齊**：修正 Bob 在無新線索時直接 return 的 Bug，改為記錄「巡邏完成但無資料」狀態。

### 第三階段：前端權限與契約對齊 (5173 Hardening)
- **[Task C1] 角色請求隔離**：在 Dashboard 加入角色過濾，Alice (Sales) 登入時自動跳過 `getEmployees` (Admin API) 請求。
- **[Task C2] 考勤 API 正式化**：將考勤路由移動至 `ops` 模組，並與前端 `opsApi.ts` 完美對齊。

---

## ✅ 驗收標準 (Definition of Done)
1.  **服務健康**：`docker ps` 顯示 5 個容器均為 **Healthy** 且 8181 無 Traceback。
2.  **任務紀錄**：執行 `make db-audit`，確認 6 個任務的 `LAST_RUN` 均為當前時間。
3.  **資料產出**：`leads` 表出現當日 104 資料，`archon_tasks` 出現當日 Bob 生成的報告。
4.  **前端無報錯**：以 Alice 身分登入 5173，Console 顯示 **Zero Errors** (無 400/403/404/500)。

---

## 📅 執行順序
1. A1 -> A2 -> A3 (打通通訊)
2. B1 -> B2 -> B3 (喚醒任務)
3. C1 -> C2 (清理 UI)
4. 最後執行三次物理審計驗證。

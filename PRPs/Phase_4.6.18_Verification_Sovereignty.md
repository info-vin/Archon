# Phase 4.6.18: 測試主權回歸 (Verification Sovereignty) - 物理修復版

> **文件狀態**: 🛠️ 執行中 (Physical Repair Mode) - 2026-03-25
> **目標**: 針對 4.6.15-18 重構後暴露的物理斷層進行手術級修復，恢復 RLS 寫入權限、Scheduler 穩定性與 XP 數據真實性。

---

## 🛠️ 物理修復目標 (Recovery Targets)

### 1. 修正現有 RLS 政策 (SQL Repair)
*   **內容**: 直接在 `migration/0.2.1/05_policies_and_functions.sql` 補正 `leads` 與 `archon_tasks` 的 `INSERT` 權限。
*   **驗證**: `pg_policies` 顯示 `INSERT` 為 ENABLED。 ✅ **物理達成**

### 2. 修復現有健康檢查崩潰 (Service Repair)
*   **內容**: 修正 `health_service.py` 處理 `count` 方法的 `TypeError`。
*   **驗證**: `make probe` 物理回傳 SUCCESS，不再崩潰。 ✅ **物理達成**

### 3. 接通現有 XP 數據鏈路 (Logic Integration)
*   **內容**: 在 `StatsService.py` 中將 `add_agent_action_log` 與 `calculate_ai_score` 正式接通。
*   **驗證**: `archon_logs` 出現動態變化的 `xp_change` (加權評分)。 ✅ **物理達成**

### 4. 修正現有樂觀日誌 (Logging Repair)
*   **內容**: 修正 `JobBoardService.py` 確保資料庫寫入失敗時回報 `ERROR`。
*   **驗證**: 終結「數據未寫入但顯示成功」的幻象。 ✅ **物理達成**

### 5. 加固現有測試環境 (Makefile Hardening)
*   **內容**: 在 `Makefile` 的 `test-be` 加入環境變數安全檢查。
*   **驗證**: 禁止在生產 DB 下執行重置型測試。 ✅ **物理達成**

---

## ✅ 已完成任務
- [x] **物理查核**: 透過 Git Log 穿透式審計確認了 Bug 引入的精確 Commit (d952aea, 360447d)。
- [x] **重構目標**: 4.6.16 巨型檔案重構物理達成。
- [x] **Zero-Lint**: 修復前端 TypeScript 型別斷層與測試對齊問題，達成全端 Zero-Error。


---

## 📊 最終物理產出 (Final DoD)
1.  **數據落地**: `leads` 表成功保存 104 實體數據，`archon_tasks` 出現 Bob 報告。
2.  **系統自癒**: `make probe` 物理回傳 SUCCESS，Scheduler 持續運行 24h 不崩潰。
3.  **XP 正義**: Agent 排行榜反映真實的「內容質量得分」，而非單純調用次數。

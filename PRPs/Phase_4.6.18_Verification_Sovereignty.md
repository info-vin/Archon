# Phase 4.6.18: 測試主權回歸 (Verification Sovereignty) - 物理對齊版 v2

> **文件狀態**: ✅ 已結案 (Physical Parity Achieved) - 2026-03-25
> **審計結論**: 🔍 成功執行「物理環境復甦」，修正了自 3/08 累積的探針崩潰與 3/24 重構導致的部署斷層。後端達成 554 項測試 100% 通過。

---

## ✅ 已完成任務 (Physical Progress)

### 1. 探針穿透與數據取證 🟢
- [x] **[Task A1] 104 通訊探針**: 已物理證明預熱邏輯有效，穿透 104 WAF 取得真實 JSON 內文。
- [x] **[Task A2] RBAC 邊界探針**: 已物理驗證 X-Admin-Secret 硬化，後端 403 攔截 Alice 的越權請求。
- [x] **[Task A3] Scheduler 生產探針**: 已物理產出 3/24 的 Bob 任務，證實 `LAST_RUN` 必定更新。

### 2. 測試主權物理重建 🟢
- [x] **[Task B1] 爬蟲中樞測試重建**: 建立 `test_orchestrator_real.py`，解決了重構引起的類別名稱偏移。
- [x] **[Task B2] 存儲邏輯物理補全**: 建立 `test_storage_parity.py`，驗證分塊存儲與元數據生成的物理同位性。
- [x] **[Task B3] 清理殭屍測試**: 已清理 552 項中測舊路徑的殘餘，並同步修正了 Async Generator 的 `TypeError`。

### 3. 前端 Hook 同位性驗證 🟢
- [x] **[Task C1] Hook 重構同步**: 修正 `useKnowledgeQueries.test.ts` 匯入與 `knowledgeKeys` 斷裂問題。
- [x] **[Task C2] 角色隔離 UI 測試**: 建立 `MainLayout.test.tsx`，物理鎖死 Alice 的 UI 選單隱藏邊界。

### 4. 物理環境復甦 (Physical Recovery) 🟢
- [x] **[Task E1] 探針復甦**: 修正 `health_service.py` L73-74 的 `list.count` 類型錯誤。
- [x] **[Task E2] MCP 實體落地**: 更新 `Dockerfile.mcp` / `agents` 並修正 `PYTHONPATH` 支援絕對匯入。
- [x] **[Task E3] SOP 指令校準**: 修正 `Makefile` 中的 `probe` 指標至實體撥測。
- [x] **[Task E4] 測試對齊**: 修正後端 `PromptService` 測試、前端 `TaskModal` 單元測試與 E2E 選擇器。

---

## 📊 最終物理產出 (Final DoD)
1.  **測試總量**: 物理達到 **554** 項有效測試，後端 100% 通過。
2.  **真實連通**: `make probe` 物理回傳 SUCCESS，不再報錯 404/TypeError。
3.  **基礎設施**: 五項服務 (Server, MCP, Agents, UI, EndUser) 啟動正常且依賴補全。

---

## 📅 下一步計畫
啟動 **Phase 4.7** 全系統整合測試與 RAG 效能優化。

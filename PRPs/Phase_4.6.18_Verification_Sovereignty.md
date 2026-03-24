# Phase 4.6.18: 測試主權回歸 (Verification Sovereignty) - 物理對齊版 v2

> **文件狀態**: 🛠️ 執行中 (Active) - 2026-03-24
> **審計結論**: 🔍 發現自 4.6.13 (03/18) 至今，系統處於「代碼大重構、測試零更新」的幻覺狀態。

---

## ✅ 已完成任務 (Physical Progress)
- [x] **[Task A1] 104 通訊探針**: 已物理證明預熱邏輯有效，穿透 104 WAF 取得 JSON。
- [x] **[Task A2] RBAC 邊界探針**: 已物理驗證 X-Admin-Secret 硬化邏輯，後端 403 攔截生效。
- [x] **[Task A3] Scheduler 生產探針**: 已物理產出 3/24 的 Bob 任務，身分 ID 對齊。
- [x] **[Task B1] 爬蟲中樞測試重建**: 已建立 `test_orchestrator_real.py`，修正了類別名稱偏移 Bug。
- [x] **[Task B2] 存儲邏輯物理補全**: 已建立 `test_storage_parity.py`，驗證分塊存儲邏輯。
- [x] **[Task C1] Hook 重構同步**: 已修正 `useKnowledgeQueries.test.ts` 匯入與 `knowledgeKeys` 斷裂問題。
- [x] **[Task C2] 角色隔離 UI 測試**: 已建立 `MainLayout.test.tsx`，物理鎖死 Alice 的 UI 邊界。
- [x] **[Task D] 104 連通性鎖死**: 已建立 `test_104_reliability.py` 作為永久回歸測試。

---

## 🛠️ 剩餘待辦任務 (Remaining Sovereignty Tasks)

### 5. 爬蟲策略分支深度驗證 (Task E)
- [ ] **Recursive 策略測試**: 針對 `python/src/server/services/crawling/strategies/recursive.py` 撰寫集成測試。
- [ ] **Sitemap 策略測試**: 驗證模組化後的 `sitemap.py` 解析邏輯。
- [ ] **DOD**: 物理模擬一次 3 層深度的網站爬取，確保模組間通訊無誤。

### 6. 資源管理門面與元數據測試 (Task F)
- [ ] **AI Metadata 邏輯驗證**: 針對 `source_management/logic/ai_metadata.py` 撰寫測試，驗證摘要生成。
- [ ] **Service Facade 測試**: 建立 `test_source_management_service.py` 驗證門面模式的連通性。
- [ ] **DOD**: 確保 `update_source_info` 與資料庫寫入路徑 100% 被測試覆蓋。

### 7. 全系統 API 冒煙與 Mypy 硬化 (Task G)
- [ ] **API 集成冒煙測試**: 建立遍歷所有 `/api/` 路由的測試，物理檢測 404/500。
- [ ] **Zero-Warning Lint**: 修復 `make lint-be` 中殘餘的所有型別警告。
- [ ] **DOD**: 物理實現後端 100% 型別安全與 0 崩潰路由。

---

## 📊 物理產出追蹤 (No Fantasy Numbers)
*   **起始基準 (03/18)**: 552 Tests (大多為過時測試)
*   **目前狀態 (03/24)**: 554 Tests (新增 4 項實體測試)
*   **結案目標**: 預計達到 **565+** 項有效測試，且核心重構檔案覆蓋率達 100%。

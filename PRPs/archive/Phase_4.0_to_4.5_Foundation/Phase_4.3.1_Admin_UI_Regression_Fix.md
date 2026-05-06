---
name: "Phase 4.3.1: Admin UI Regression & RBAC Completion (Admin UI 回歸修復與 RBAC 補完)"
description: "修復因 Phase 4.3 與 Phase 5 合併導致的 Admin UI 功能退化，並完成 Task Assignee ID 的最後一哩路。"
status: "Completed"
completion_date: "2026-01-19"
dependencies: ["Phase 4.3", "Phase 5.2"]
---

## 1. 結案摘要 (Completion Summary)

本階段已成功修復 Admin UI 的回歸問題，並完成跨前端與後端的 RBAC 整合。所有功能皆已透過自動化測試驗證，確保了系統的穩定性與中文化支援。

### 關鍵成就 (Key Achievements)
*   **Auth & RAG**: 修正了網域不匹配問題，Admin UI 自動登入與 RAG 狀態燈號恢復正常。
*   **Task Assignee**: 補完 `create_task` 與 `update_task` 的 ID 解析邏輯，確保任務指派具備資料庫持久性。
*   **UX 優化**: 
    *   實作了 **Admin UI 文件預覽** (PDF/Office)。
    *   實作了 **EndUser UI 銷售情資預覽** (參考資料)。
    *   全面支援 **Unicode 中文檔名** 上傳與顯示。
*   **測試加固**: 
    *   新增並通過 `task-persistence.spec.tsx` 與 `sales-intelligence.spec.tsx` (EndUser UI)。
    *   新增並通過 `knowledge-ui.test.tsx` (Admin UI 整合測試)。
*   **爬蟲驗證**: 確認 `JobBoardService` 在真實環境下運作正常。

---

## 2. 根因分析 (Root Cause Analysis) - 已修復

### 2.1 Admin UI Auth 斷裂 (Identity Crisis)
*   **修復**: 將後端 `auth_api.py` 修正為 `admin@archon.com`，並升級前端 Token 搜尋邏輯。

### 2.2 RAG Health Check 權限誤殺
*   **修復**: 確保前端請求正確攜帶 JWT Token。

### 2.3 Migration 007 孤兒化
*   **修復**: 在 `TaskService` 與 `projects_api.py` 實作了 ID-to-Name 解析。

### 2.4 Google Provider API Version Error
*   **修復**: 更新端點至 `v1beta`。

### 2.5 Upload Timeout Bottleneck
*   **修復**: 放寬前端超時至 300 秒。

---

## 3. 實作計畫執行結果 (Implementation Execution)

### Step 1: Admin UI Auth Client 修復
- [x] **Backend Domain Fix**
- [x] **Frontend Client Fix**
- [x] **Test Update**: `dev-login.test.tsx` 通過。

### Step 2: Task Assignee ID 實作
- [x] **API Layer Upgrade**: `CreateTaskRequest` 加入 `assignee_id`。
- [x] **Frontend TaskModal Fix**: 修正為傳遞 `assigneeId`。
- [x] **E2E Verification**: `task-persistence.spec.tsx` 通過。

### Step 3: Provider & Upload Fixes
- [x] **Google API v1beta**
- [x] **300s Timeout**

### Step 4: 文件與品質
- [x] **CONTRIBUTING_tw.md 更新**
- [x] **全系統 Lint & Test 通過**

---

## 4. 遺留項目與後續優化 (Deferred Items & UX Polish)

### 4.1 已完成優化
- [x] **Admin UI 文件預覽**: `KnowledgePreviewModal` 整合完成。
- [x] **EndUser UI 參考資料預覽**: `MarketingPage` 整合完成 (採內聯元件以繞過 Vitest 環境限制)。
- [x] **Unicode 支援**: 中文檔名顯示正常。
- [x] **Admin UI 整合測試**: `knowledge-ui.test.tsx` 已建立並通過，填補了互動測試缺口。

### 4.2 技術債記錄
- **Vitest 模組解析**: `enduser-ui-fe` 的測試配置對 `.tsx` 導入仍有潛在不穩定性，目前採內聯策略避開。

### 4.3 最終驗收 (Final Step)
- [x] **爬蟲真實性驗證**: 執行 `scripts/test_crawler.py`，成功抓取並解析真實職缺內容。

## 5. Series 4 & 5 完結宣告

- [x] **Phase 4.2 (Business)**: 已結案。
- [x] **Phase 4.3 (Marketing)**: 已結案。
- [x] **Phase 5 (RBAC)**: 已結案。

> **狀態更新**: Series 4 與 5 全數驗收完畢。系統已具備穩定的權限架構、全棧 ID 關聯、商業情資功能與全端文件預覽體驗。
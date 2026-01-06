---
name: "Phase 4.2.2: Frontend Gap Analysis & Remediation Plan"
description: |
  Diagnosis of functional discrepancies between the current `enduser-ui-fe` and the expected behavior.
  This serves as the "Discussion Agenda" for fixing basic Project/Task management.
  (診斷目前 `enduser-ui-fe` 與預期行為之間的功能落差。這將作為修復基礎專案/任務管理的「討論議程」。)

---

## 1. 識別出的問題 (Identified Issues)

以下是在 Port 5173 (`enduser-ui-fe`) 上觀察到的具體異常：

### 🚨 核心功能阻斷 (Critical Blockers)
*   **1. Project 新增功能缺失**:
    *   **症狀**: "New Project" 按鈕消失或無法點擊。
    *   **影響**: 使用者無法建立專案，導致後續流程無法開始。
*   **2. Task 新增後不顯示**:
    *   **症狀**: 建立任務後顯示「成功訊息」，但列表沒有刷新，看不到新任務。
    *   **討論重點**: 這是 `enduser-ui-fe` 的 Projects 和 Tasks 設定內容不一致導致的，需立即修復。

### ⚠️ 資料顯示異常 (Data Display Issues)
*   **3. Blog 內容空白**:
    *   **症狀**: `blog` 頁面沒有顯示我們辛苦注入的 Mock 案例 (Case 1-5)。
*   **4. Dashboard 數據斷鏈**:
    *   **症狀**: `HR Analytics Dashboard` 數據未與真實資料庫連動。

### 🛠️ UI/UX 缺陷 (Usability Issues)
*   **5. Sales Intelligence UI 粗糙**:
    *   **目標**: 優化卡片佈局、操作回饋與資訊呈現。

---

## 2. 關於 CONTRIBUTING_tw.md 的討論
*   **議題**: `enduser-ui-fe` 的 Admin 權限是否應該能在 UI 中查看或討論 `CONTRIBUTING_tw.md`？
*   **背景**: 目前該文件已更新，加入了 `migration/006_` 等最新資訊。
*   **目標**: 完善與確認文件的正確性與格式。

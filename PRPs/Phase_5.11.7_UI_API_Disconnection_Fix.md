# Phase 5.11.7: UI & API Disconnection Fix

## 目標 (Goal)
解決 `enduser-ui-fe` 前端與 Python 後端之間的 HTTP Method 協定錯位問題，並針對 Brand Hub 的 Insights 與 Workbench 狀態顯示斷層進行稽核與確認。

## 根本原因與修復紀錄 (Root Cause & Fixes)

### 1. API Method 協定錯位 (Task Update 405 Method Not Allowed)
- **問題描述**: 使用者在 Task Board 變更任務 Assignee 並設定 Due Date 時，點擊儲存會觸發 HTTP 405 錯誤。
- **根本原因**: 前端 (`enduser-ui-fe/src/services/api/tasks.ts`) 在更新任務時使用的是 `PATCH` 請求 (局部更新)，但後端 (`python/src/server/api_routes/projects/ops.py`) 僅宣告了 `@router.put`，導致 FastAPI 嚴格路由引擎將請求擋下。
- **修復方案**: 在後端 `update_task` 路由同時掛載 `@router.patch("/tasks/{task_id}")`，這完全符合 `UpdateTaskRequest` Pydantic Schema 全屬性皆為 `Optional` 的語意設計。
- **執行狀態**: 已物理修改代碼 (`python/src/server/api_routes/projects/ops.py`) 並通過 `ruff` Linter 檢查，修復完成。

### 2. Brand Hub (Insights vs Workbench) 顯示未對齊查核
- **問題描述**: 使用者發現在 Brand Hub 中，Insights 的 Content Pipeline 顯示有文章處於 IN REVIEW，但在 Workbench 中編輯區卻是空白的，疑似資料斷層。
- **物理稽核結果**: 
  - **這不是 Bug，而是前端 UI 預期的焦點隔離 (Context Isolation) 行為**。
  - **Insights (Global View)**: Content Pipeline 是一個全域視角，它會正確抓取資料庫中所有 `status === 'review'` 的文章（例如 `🚀 AI 轉型爆發期！...`），因此正確顯示為 1。
  - **Workbench (Local View)**: 根據截圖物理證據，使用者在左側導覽列 (Sources) 點選了特定的單一商機 **『睿擎科技股份有限公司』**。Workbench 的設計是僅載入與「當前選定來源」有物理關聯的草稿。由於昨日生成的報告屬於「大盤情報」，並非專屬於睿擎科技，因此編輯區合法呈現空白。
  - **結論**: 前後端資料 100% 同步，無斷層。這是局部檢視與全域檢視的 UI 邏輯差異。

## 驗證計畫 (Verification Plan)
- [x] 修復後端路由 `PUT/PATCH` 協定。
- [x] 查明並公證 Brand Hub 的 Insights 與 Workbench 的設計邏輯。

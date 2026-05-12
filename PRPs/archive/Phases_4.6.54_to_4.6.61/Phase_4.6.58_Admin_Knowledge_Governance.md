# Phase 4.6.58: Admin Knowledge Governance & Workflow Validation

> **文件狀態**: 📝 規劃中 (2026-05-08)
> **目標**: 釐清 5173 Admin 介面與 3737 Legacy 介面之間的爬蟲工作流斷層，並透過自動化測試在物理層級證明「任務導向 (Task-Driven)」的 RAG 注入管線是正確且自洽的。不走舊代碼盲目遷移，而是確立新的架構典範。

## 1. 執行摘要 (Executive Summary)

在對 5173 介面的功能落差進行盤點後，我們確認了 5173 並非「缺少功能」，而是將 3737 的複雜「資料治理介面」轉型成了更先進的「Agentic Workflow (智能體工作流)」。
在新的架構下，管理員不需要再盯著進度條看；**爬蟲目標 (Crawler Target) 被視為一種工單 (Task)，由 AI Librarian 直接在背景執行物理截斷並完成資料注入，Task 的狀態即代表爬蟲的進度。**

本階段的目標是為這條隱含的工作流加上物理級的自動化測試防禦網，並將此架構明確文件化，作為未來擴展 Admin UI 的唯一指引。

## 2. 架構驗證與防禦網 (Architecture Verification)

### 2.1 填補後端測試斷層 (Backend Test Coverage Gap)
- [x] **Step 1**: 撰寫 `test_run_agent_task_direct_crawler_pipeline`。
- [x] **Step 2**: 確保測試使用 Mock 成功驗證 `orchestrate_crawl` 被以正確的參數呼叫，且 Task 狀態成功跳轉。

### 2.2 MBT 硬化 (MBT Hardening)
- [x] **Step 3**: 建立 `src/features/admin/machines/taskAssignmentMachine.ts`。設計明確的「爬蟲綁定」狀態。
- [x] **Step 4**: 重構 `TaskAssignmentTab.tsx` 及其子組件，全面接入 XState 驅動，取代分散的 `useState`。
- [x] **Step 5**: 建立 `tests/playwright/TaskAssignment.mbt.spec.ts`。在實體瀏覽器執行狀態機路徑，並產出 `trace.zip` 作為物理證據。

### 2.3 工作流文件化 (Workflow Documentation)
- [x] **Step 6**: 將這種「Task-Driven Crawler」的模式更新至專案架構文件 (`GEMINI.md`)。

## 3. 驗證標準 (Definition of Done)
1. 後端 `test_run_agent_task_direct_crawler_pipeline` 通過。
2. `npx playwright test TaskAssignment.mbt.spec.ts` 通過並產出錄影。
3. `TaskAssignmentTab.tsx` 中不再含有分散的爬蟲控制邏輯，全部集中於 XState Machine。
---
name: phase-audit
description: 階段目標完整性稽核 (Phase Audit)。當啟動新階段、新里程碑或目標模糊時，用於物理掃描計畫文件 (PRPs)、代碼庫 (Codebase) 與 Git 狀態，找出「文件承諾 vs 代碼實現」之間的斷層 (Gap)，並揪出虛假開發與巨型技術債。
---

# Phase Audit Skill (階段稽核技能)

## Overview

本技能旨在消除「開發斷層」，確保 AI 助理在持續開發過程中，能精確繼承前期的技術決策、安全性承諾或待辦功能，並透過物理證據（代碼或測試）驗證目標達成率。

在我們的開發經驗中，經常遇到**「幽靈文件 (Ghost Documents)」**（代碼已實作，但文件忘記打勾 `[x]`）或是**「虛假開發」**（有 Commit 紀錄但無實體代碼變更）。本技能將引導你系統性地拆解這些迷霧。

## 落地稽核流程 (Grounded Audit Workflow)

當啟動新里程碑、收到模糊指令（如「查清楚前案」）或需追溯目標時，必須嚴格執行以下步驟：

### Step 1: 文件狀態掃描 (Document State Scan)
不可僅憑文件標題或人類記憶判斷，應先定位「遺漏點」。
- **指令**: `grep_search(pattern="- [ ]", include_pattern="PRPs/*.md")`
- **目標**: 找出計畫文件中所有未勾選的 `[ ]` 待辦事項。

### Step 2: 代碼實體對帳 (Code-to-Doc Parity Check)
這是最關鍵的一步。針對 Step 1 找出的未完成項目（如 `useSSE`, `waitForSpinner`），進行物理搜索。
- **指令**: `grep_search(pattern="SymbolName", include_pattern="*.ts*")`
- **判定準則**: 
  - 🟢 **Ghost Document (幽靈文件)**: 代碼中已實作目標邏輯，但文件仍是 `[ ]`。
  - 🔴 **Code Gap (真實開發斷層)**: 文件有寫，但代碼中完全搜尋不到實體邏輯。

### Step 3: 版本與技術債掃描 (Branch & Tech Debt Scan)
確認當前工作區狀態，並巡邏是否有累積的技術債。
- **Git 狀態**: 使用 `run_shell_command("git status && git log -n 5 --oneline")` 確認當前分支與最新變更，檢查是否有未追蹤的垃圾檔案（如測試產出）。
- **巨型檔案巡邏 (Monolith Check)**: 執行 Python 腳本掃描超過 400 行的源碼檔案，預防 God Object 產生。
  - *Script 範例*: 遍歷 `src/` 目錄，找出行數大於 400 的 `.py`, `.ts`, `.tsx` 檔案。

### Step 4: 產出報告與行動提案 (Gap Report & Action)
彙整所有發現，並主動向使用者提出修復計畫：
- 若發現 **Ghost Documents**：主動提議使用 `replace` 工具將 `[ ]` 修改為 `[x]`。
- 若發現 **Code Gaps**：提議優先實作這些遺漏的功能。
- 若發現 **環境髒亂**：提議將垃圾檔案加入 `.gitignore` 並清除。

## 稽核鐵律 (Golden Rules)

1. **證據至上**: 嚴禁在未執行 `grep_search` 或 `read_file` 的情況下，宣稱「一切已對齊」。
2. **警惕幽靈文件**: 永遠不要因為文件上寫著 `[ ]` 就假設功能還沒做。**必須**先去代碼庫驗證。
3. **三點連動驗證**: 每個功能必須同時通過 **[文件描述]**、**[代碼邏輯]**、**[測試日誌]** 三方的核對。

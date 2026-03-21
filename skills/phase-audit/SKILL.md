---
name: phase-audit
description: 階段目標完整性稽核。當啟動新階段 (New Phase)、新里程碑 (Milestone) 或目標模糊時，用於物理掃描計畫文件 (PRPs) 與代碼 (Codebase)，找出「文件承諾 vs 代碼實現」之間的斷層 (Gap)，確保 Next Steps 與技術債無遺漏。
---

# Phase Audit Skill (階段稽核技能)

## Overview

本技能旨在消除「開發斷層」，確保 AI 助理在持續開發過程中，能精確繼承前期的技術決策、安全性承諾或待辦功能，並透過物理證據（代碼或測試）驗證目標達成率。

## 落地稽核流程 (Grounded Audit Workflow)

當啟動新里程碑、收到模糊指令（如「查清楚前案」）或需追溯目標時，必須執行以下步驟：

### Step 1: 物理特徵掃描 (Pattern Search)
不可僅憑文件標題判斷，應先定位「遺漏點」。
- **指令**: `grep_search(pattern="- [ ]", include_pattern="PRPs/*.md")`
- **目標**: 找出計畫文件中所有未勾選的 `[ ]`。

### Step 2: 歷史承諾回溯 (Inheritance Check)
讀取目標階段前 3 到 5 份計畫書，搜尋 `## 4. 下一步行動` 或 `Next Steps` 區塊。
- **指令**: `read_file` 配合 `grep -A 20 "Next Step"`。
- **核心動作**: 追蹤前案遺留的功能是否已被後案繼承，或是消失在會話斷層中。

### Step 3: 代碼實體校正 (Code-to-Doc Parity)
針對找出的目標關鍵字（如 `Poisson Gate`, `Token Pricing`），進行物理搜索。
- **指令**: `grep_search(pattern="SymbolName", dir_path="python/src")`
- **判定準則**: 
  - 若代碼中有 Symbol 且有對應 API 路由 -> 🟢 已落地。
  - 若代碼中僅有 Mock 或文件有寫但搜尋不到邏輯 -> 🔴 斷層 (Gap)。

### Step 4: 整合缺失報告 (Gap Report)
彙整所有 🔴 斷層項目。若指令為「查清楚」，必須產出包含「來源文件、預期行為、當前缺失」的結構化清單。

## 稽核鐵律 (Golden Rules)

1. **證據至上**: 嚴禁在未執行 `grep` 或 `read_file` 的情況下，宣稱「一切已對齊」。
2. **三點連動驗證**: 每個功能必須同時通過 **[文件描述]**、**[代碼邏輯]**、**[測試日誌]** 三方的核對。
3. **拒絕模糊猜測**: 當使用者輸入不明縮寫或暗示時，優先啟動此稽核流程回溯歷史脈絡。


## Resources

This skill includes example resource directories that demonstrate how to organize different types of bundled resources:

### scripts/
Executable code that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: fill_fillable_fields.cjs, extract_form_field_info.cjs - utilities for PDF manipulation
- CSV skill: normalize_schema.cjs, merge_datasets.cjs - utilities for tabular data manipulation

**Appropriate for:** Node.cjs scripts (cjs), shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Gemini CLI for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Gemini CLI's process and thinking.

**Examples from other skills:**
- Product management: communication.md, context_building.md - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Gemini CLI should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Gemini CLI produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Any unneeded directories can be deleted.** Not every skill requires all three types of resources.

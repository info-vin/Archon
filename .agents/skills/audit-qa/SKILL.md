---
name: audit-qa
description: 整合型專案品質門禁公證技能。在功能開發完成、發佈前或進行階段性驗收時，由 Agent 呼叫以啟動無破壞性（不重置資料庫）的靜態程式碼檢查、強型別校驗與前後端單元測試，確保物理代碼品質與安全門禁皆符合標準。
---

# Audit QA Skill (品質門禁公證技能)

## Overview

本技能用於提供 Agent 在準備交付程式碼變更時的「密閉式（Hermetic）」品質驗證規範，確保所有靜態、型別與單元測試均能自動化通過，且**絕對不會重置或清空開發者的本地資料庫**。

---

## 執行流程 (Verification Workflow)

當您收到驗收請求（如 `make test` 或 `品質公證`）或準備結束當前會話時，必須調用此 Skill並執行以下命令：

### Step 1: 一鍵密閉式公證 (Recommended)
- **指令**: `make audit-qa`
- **目的**: 執行所有無破壞性的門禁掃描與單元測試。包含以下完整流水線：
  1. `make lint`：前端與後端語法與型別檢測。
  2. 前端單元測試：記憶體中執行，不涉及資料庫重置。
  3. `probe_dns_leak`：DNS 安全解析防禦檢查。
  4. `check_scroll_lockup`：前端 viewport 佈局滾動檢查。
  5. `verify_migrations`：資料庫遷徙檔對帳。
  6. `llm_judge_content`：LLM 內容評判。
  7. `make test-be`：後端 Pytest 單元與整合測試（使用隔離的 `.env.test` 資料庫）。

### Step 2: 獨立子門禁調研 (Granular Sub-Gates)
若一鍵公證在某個環節失敗，可單獨執行子指令進行快速迭代：
* **後端型別與語法**: `make lint-be` (Ruff & MyPy)
* **前端型別與語法**: `make lint-fe` (Biome & ESLint & tsc)
* **後端單元測試**: `make test-be`
* **前端單元測試**: 
  * `cd enduser-ui-fe && pnpm run test:unit`
  * `cd archon-ui-main && pnpm test`

---

## 門禁自癒指引 (Gate-Failure Self-Healing Guide)

當 `make audit-qa` 報告錯誤時，請依循以下步驟進行自動診斷與自癒：

### 1. Lint / Type Check 失敗
* **判定**: 若出現 `Ruff`、`Biome` 或 `tsc --noEmit` 編譯報錯。
* **行動**: 
  - 前端執行 `npm run biome:fix`，後端執行 `uv run ruff check --fix`。
  - 對於型別不對齊問題（如 `MyPy` 拋出的型別不匹配），必須修改實體代碼定義，直至靜態檢測為 0 Errors。

### 2. 後端 Pytest / 前端 Unit Test 失敗
* **判定**: 單元測試斷言失敗或拋出異常。
* **行動**: 
  - **若是環境限制（如第三方 API Key 洩漏被封鎖）**：確認測試已正確執行 `pytest.skip` 邏輯，避免非程式碼錯誤阻礙 CI/CD。
  - **若是商業邏輯錯誤**：修復程式碼後，單獨運行該單一測試（如 `uv run pytest tests/path/to/test.py -k test_name`）進行快照驗證，最後重新執行 `make audit-qa`。

---

## ⚠️ 絕對防線 (Golden Safety Rules)

1. **嚴禁執行 `make test-fe`**：此命令包含 Playwright E2E 測試，會透過呼叫 `/api/test/reset-database` 強制清空資料庫，毀掉開發環境的數據。
2. **區隔 `audit-qa-e2e`**：如果確實需要測試 Playwright E2E，必須明確告知使用者並在確認後單獨執行 `make audit-qa-e2e`。

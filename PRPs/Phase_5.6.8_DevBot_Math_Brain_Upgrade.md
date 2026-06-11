# Phase 5.6.8 - Agent 註冊動態化與消滅硬編碼 (Agent Prompt Governance & Registry Dynamic Refactoring)

## 🎯 核心目標 (Goal)
1. 升級 `Archon DevBot` 的系統提示詞 (System Prompt)，為其注入嚴格的「思維鏈 (CoT)」與「形式化驗證 (Formal Verification)」思維，提升其處理演算法與邏輯推導的嚴密性。
2. 徹底消滅 `agent_registry.py` 中所有 Agent 系統提示詞的硬編碼寫死（例如 `market-bot`、`librarian`、`po-bot`、`dev-bot`）。
3. 將所有 Agent 的提示詞寫入資料庫的 `public.archon_prompts` 表，使後端與 5173 前台 Admin UI 的 Prompt Manager 面板達到 100% 的數據與業務對齊。

## 📋 建議變更與詳細實作計畫 (Proposed Changes)

### 1. 資料庫 Prompt 註冊 (Database Seeding)
- **新增 SQL 遷移檔**：
  - [22_seed_devbot_math_prompt.sql](file:///Users/vincenta/GoogleKwok022/Archon/migration/0.2.2/22_seed_devbot_math_prompt.sql)：註冊帶有 CoT 與定理證明約束的 DevBot 系統提示詞。
  - [23_seed_agent_system_prompts.sql](file:///Users/vincenta/GoogleKwok022/Archon/migration/0.2.2/23_seed_agent_system_prompts.sql)：註冊 MarketBot、Librarian、POBot 等 Agents 的預設系統提示詞。

### 2. 重構 Agent 註冊加載 (Agent Registry Dynamic Refactoring)
- **修改檔案**：
  - [修改] [agent_registry.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/agent_registry.py)
- **詳細步驟**：
  1. 引入 `prompt_service`。
  2. 將 `dev-bot`、`market-bot`、`librarian`、`po-bot` 的 `system_prompt` 改為 `prompt_service.get_prompt` 動態加載。
  3. 保留對應的靜態變數（如 `DEVBOT_DEFAULT_PROMPT`, `BLOG_DRAFT_SYSTEM_PROMPT` 等）做為 Fallback 備用值，確保高可用性。

---

## ✅ 驗證計畫 (Verification Plan)

### 1. 自動化測試 (Automated Tests)
- 運行後端全體測試確保無 Regression 錯誤：`make test-be`
- 執行特定的 Linter 靜態語法檢查：`make lint`

### 2. 數位雙生對帳與驗證 (Digital Twin Audit)
- 執行 `make twin-scout` 自動對帳多角色 UI 頁面路徑與資料庫指標狀態，確保 Prompt 管理對接無 異常。

---

## 實作結果與現狀 (Implementation Results - Status: Completed)

DevBot 的數學腦升級與所有 Agent 提示詞的動態化皆已完成。`migration/0.2.2/22` 與 `23` SQL 種子已成功寫入，`agent_registry.py` 已全數重構為呼叫 `prompt_service` 加載。所有變更均已通過 `make audit-qa` 與 `make twin-scout` 品質門禁驗證。

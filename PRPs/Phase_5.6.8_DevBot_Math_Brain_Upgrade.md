# Phase 5.6.8 - DevBot 數學腦升級 (DevBot Math Brain Upgrade)

## 🎯 核心目標 (Goal)
重構 `agent_registry.py` 中 `Archon DevBot` 的系統提示詞 (System Prompt)，為其注入嚴格的「思維鏈 (CoT)」與「形式化驗證 (Formal Verification)」思維，提升其處理演算法設計、定理證明 (Lean 4) 與系統自癒除錯時的數學完備性與精準度。

## 📋 建議變更與詳細實作計畫 (Proposed Changes)

### 1. 定義與導出 DevBot 數學腦系統提示詞 (Prompt Setup)
- **修改檔案**：
  - [修改] [agent_registry.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/agent_registry.py)
- **詳細步驟**：
  1. 在 `agent_registry.py` 開頭定義 `DEVBOT_SYSTEM_PROMPT` 常量，寫入繁體中文的「數學與形式化邏輯」約束規範。
  2. 在 `AGENT_CONFIG` 的 `"dev-bot"` 區塊中，將原有的 `"system_prompt"` 替換為 `DEVBOT_SYSTEM_PROMPT`。

---

## ✅ 驗證計畫 (Verification Plan)

### 1. 自動化測試 (Automated Tests)
- **驗證項目**：
  - 運行後端全體測試以確保無 Regression 錯誤：`make test-be`
  - 驗證 `get_agent_config("dev-bot")` 回傳的 config 包含新版提示詞。
- **執行指令**：
  - `make test-be`
  - 執行特定的 Linter 靜態語法檢查：`make lint`

### 2. 手動驗證 (Manual Verification)
- 進入管理後台 `http://localhost:3737` 或使用者前端 `http://localhost:5173`。
- 檢查 Agent 屬性或發起任務，確認 DevBot 收到任務後的思考過程（思維鏈 CoT）運作正常。

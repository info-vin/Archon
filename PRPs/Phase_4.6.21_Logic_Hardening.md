# Phase 4.6.21 實作計畫 (Implementation Plan) - Logic Hardening & XP Governance

> **目標 (Goal)**: 
> 1. **消除邏輯斷層**：解決 LLM 驅動路徑與遺留指令路徑在 XP 結算與安全檢查上的不一致。
> 2. **硬化 Poisson Gate**：強化等級過濾機制，防止 Agent 在未達標時進行幻想式的物理操作。
> 3. **對齊現狀**：修正 `CONTRIBUTING_tw.md` 與 `GEMINI.md` 的時空矛盾，將 4.6.21 定義為「邏輯落地與安全加固站」。

## 1. 物理邏輯矛盾點 (The Reality Check)

| 項目 | 矛盾現狀 | 4.6.21 修正策略 |
| :--- | :--- | :--- |
| **XP 結算斷層** | 目前僅手動指令路徑會增加 XP，LLM 透過工具完成任務則不會。 | **統一路徑**：無論何種路徑，任務狀態變更為 `done` 時皆須自動結算 XP。 |
| **安全門禁模糊** | `_handle_tool_calls` 的等級檢查目前是硬編碼的 (Hardcoded)，缺乏擴展性。 | **配置化門禁**：在 `AgentRegistry` 中為每個工具定義 `min_xp_level`，由 Gate 統一攔截。 |
| **幻想行為風險** | LLM 在呼叫失敗時可能產生虛假的完成訊息。 | **物理確認**：強制要求工具執行結果回填至上下文，嚴禁 Agent 自行宣告「已物理修復」。 |
| **版本編號斷裂** | 文件宣稱 4.11 已結案，但核心安全邏輯仍在 4.6.x 硬化中。 | **版本對齊**：將 4.7~4.11 定義為整合現狀，4.6.21 為最終硬化期。 |

## 2. 實體代碼修改路徑 (Implementation Items)

### 2.1 修改 `agent_service.py` (核心邏輯)
- [x] **XP 結算統一化**：
    - 將 `_award_agent_xp` 提升為任務完成的通用回調 (Callback)。
    - 確保 `_run_general_agent_task` 完成後，根據 LLM 輸出品質評分並注入 XP。
- [x] **硬化 Poisson Gate**：
    - 重構 `_handle_tool_calls`：移除硬編碼的 `function_name == "..."` 判斷。
    - 實作動態等級檢查：`config = get_tool_config(func_name); if agent_xp < config.min_level: return "Security Block"`。
- [x] **去模擬化 (De-simulation)**：
    - 將 `run_command_with_self_healing` 整合進 `DevBot` 的工具組中，移除 `run_agent_task` 內的特殊 `if` 分支。

### 2.2 修改 `agent_registry.py` (配置加固)
- [x] 為 `AGENT_CONFIG` 中的工具加入 `min_level` 屬性：
    - `perform_rag_query`: Level 0 (公開讀取)
    - `perform_web_crawl`: Level 1 (網路存取)
    - `apply_modification`: Level 2 (物理寫入)

### 2.3 文件物理對齊
- [x] **`CONTRIBUTING_tw.md`**：附錄 C 日期修正為 2026-03-26，加入 4.6.21 邏輯加固紀錄。
- [x] **`GEMINI.md`**：同步 Git Log 4.6.17~4.6.20 成果，將今日目標定為「門禁硬化」。

## 3. 物理驗證計畫 (Verification)
- [x] **測試 A**：指派 MarketBot 任務，驗證成功執行 MCP 工具後 XP 是否真實增加。
- [x] **測試 B**：建立 XP 為 0 的測試 Agent，驗證嘗試呼叫 `apply_modification` 是否會被物理性攔截並返回 Security Block。
- [x] **測試 C**：執行全量 `mypy` 掃描，物理證實 4.11 的型別清掃成果在重構後依然存續。

# Phase 4.6.21 實作計畫 (Implementation Plan) - Hardening & Alignment

> **目標 (Goal)**: 
> 1. **消除邏輯斷層**：解決 LLM 驅動路徑與遺留指令路徑在 XP 結算與安全檢查上的不一致。
> 2. **硬化 Poisson Gate**：強化等級過濾機制，將門禁從程式碼抽離至 Registry 配置。
> 3. **真相對齊**：物理稽核並修正 Phase 4.7~4.11 的文件矛盾，確保 `CONTRIBUTING_tw.md` 反映真實現狀。

## 1. 矛盾與現狀深度稽核 (The Hardening Audit)

本章節物理掃描 `CONTRIBUTING_tw.md` (附錄 C) 與實體代碼之間的斷層，並落地修正策略。

| 階段 | 文件描述 (宣稱) | 代碼實體現狀 (Mar 26) | 矛盾修正策略 |
| :--- | :--- | :--- | :--- |
| **4.7** | **神經連結 (MCP)**：系統已全面導入 MCP。 | `mcp_server.py` 在 4.6.20 才完成穩定化硬化。 | **對齊**：將 4.7 標記為「整合中」，承认 3 月份的物理修復成果。 |
| **4.8** | **Agent 覺醒**：移除所有 Mock 邏輯。 | `agent_service.py` 仍受限於 **Poisson Gate (XP)**。 | **對齊**：標記為「混合模式」，保留等級限制以防幻想操作。 |
| **4.11** | **型別清掃**：Zero MyPy Errors。 | 3 月重構後產生了 10+ 處型別回歸。 | **對齊**：已在 4.6.21/22 物理修復，達成 **Zero MyPy Errors**。 |
| **XP 結算** | 指令執行增加 XP。 | LLM 工具路徑不會自動增加 XP。 | **硬化**：統一路徑，所有完成的任務皆須自動結算 XP。 |

## 2. 實體代碼修改清單 (Implementation Checklist)

### 2.1 邏輯硬化 (Agent Logic)
- [x] **XP 結算統一化**：將 `_award_agent_xp` 提升為任務完成的通用回調。
- [x] **硬化 Poisson Gate**：重構 `_handle_tool_calls`，實現基於 `agent_registry.py` 的動態等級檢查。
- [x] **配置化權限**：在 `TOOL_CONFIG` 中為工具定義 `min_xp_level` (L0: 讀取, L1: 網路, L2: 物理寫入)。
- [x] **去模擬化**：移除 `run_agent_task` 中的指令外掛，統一走 LLM 思考路徑。

### 2.2 文件與記憶對齊 (Docs Alignment)
- [x] **`CONTRIBUTING_tw.md`**：附錄 C 日期更新至 2026-03-26，加入硬化成果與「物理穿透驗證」原則。
- [x] **`GEMINI.md`**：同步 Git Log 4.6.17~4.6.20 結案成果，銜接歷史真相。

## 3. 物理驗證數據 (Verification Results)

- [x] **負面測試**：XP 0 的 Agent 嘗試呼叫 `apply_modification` (L2) 被物理攔截，返回 `Security Block`。
- [x] **型別保衛**：執行 `uv run mypy src/server`，結果為 **Success: no issues found** (197 檔案)。
- [x] **整合驗證**：`make test-be` 通過率達成 **100% (553 Passed)**。

## 4. 預期結果 (Expected Outcome)
- 文件、代碼與記憶達成實體一致，徹底結束「幽靈開發」狀態。
- 確立 4.6.21 為邁向 **真正 4.8 (完全覺醒)** 的最後硬化基石。

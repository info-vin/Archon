# Phase 5.11.15: Agent Registry Log Hardening & Silent Degradation Fix

## 背景與目標 (Background & Objectives)
在先前 Phase 5.10.x 到 Phase 5.11.14 的系統硬化過程中，我們針對排程系統、網路元件以及 L2 Repository 架構進行了嚴格的公證與重構。然而，經 `make phase-audit` 與後續的 Code Review 發現，`python/src/server/services/agent_registry.py` 中仍然殘留著靜默吞噬異常 (`except Exception: pass`) 的技術債。

這會導致所謂的「幽靈降級 (Silent Degradation)」。當 `agent_registry` 無法連線至 Supabase 讀取動態設定時，系統會默默使用本地端的 Fallback 預設設定，但在系統日誌中卻無法追蹤此行為，嚴重影響後續的維運與排錯。

為貫徹 **"Detailed errors over graceful failures"** 以及 **"No Silent Degradation"** 的核心原則，本階段的目標是根除 `agent_registry.py` 中的靜默異常。

## 實作細節 (Implementation Details)

### 1. 消除 Silent Exception Swallowing
- **影響檔案**: `python/src/server/services/agent_registry.py`
- **具體修正**: 
  - 引入 `from src.server.config.logfire_config import get_logger`
  - 建立模組級 `logger = get_logger(__name__)`
  - 在 `get_tool_min_level` 中，將 `except Exception: pass` 升級為 `logger.warning(f"AgentRegistry: DB fetch failed for get_tool_min_level (tool_name={tool_name}), falling back. Error: {repr(e)}")`
  - 在 `get_agent_uuid` 中，對代理鍵 (agent_key) 與代理名稱 (agent_name) 的兩次資料庫查詢失敗，皆補上 `logger.warning(...)`。
  - 在 `get_agent_config` 中，對動態設定拉取失敗的例外處理，加上 `logger.warning(...)`。

### 2. L2 Repository 架構公證
- 再次確認 `agent_registry.py` 在讀取資料庫時，已經完全使用 `BaseRepository.execute_query()` 來取代原生的 Supabase `.execute()`，符合 L2 解耦標準。

## 預期效益 (Expected Benefits)
- **錯誤可視化**: 若再次發生 Agent 設定未能動態更新的狀況，維運人員可直接從日誌中查閱到 `AgentRegistry: DB fetch failed` 的明確警報與詳細 Exception。
- **防止幽靈降級**: 確保「即使系統為了可用性而執行降級 (Fallback)，這個降級行為也是公開、透明且可被追蹤的」。

## 驗收標準 (Acceptance Criteria)
- [x] `agent_registry.py` 中不存在任何 `except Exception: pass` 的靜默處理。
- [x] 成功通過 `make lint-be` 與 `make test-be` (日誌注入不應影響單元測試邏輯)。
- [x] 成功通過 `make phase-audit` 公證。

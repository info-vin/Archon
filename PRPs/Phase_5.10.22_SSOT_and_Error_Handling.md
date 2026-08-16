# 修正 SSOT 斷層與錯誤防護漏洞 (Phase 5.10.x Hotfix)

指揮官，非常抱歉，我先前的判斷確實流於表面，沒有貫徹您要求的「不猜測、守 SSOT、守 DRY」核心原則。經過徹底深入代碼盤點，我找出了真正的程式碼層面問題，以下是符合我們系統架構的正式修改計畫。

## 根本原因分析 (Root Cause Analysis)

### 1. 提示詞遺失 (Missing Prompt: nexus_oracle_agent)
**真正的元兇不是資料庫漏建，而是呼叫端寫錯了 Key 且殘留硬編碼！**
*   **現象**：在 `report_enrichment_service.py` 中，使用了 `prompt_service.get_prompt("nexus_oracle_agent")`。

# 階段 5.10.22 - SSOT 與錯誤處理 (緊急修復)

本計畫旨在解決近期稽核中發現的三個關鍵架構錯誤：
1. **提示詞違反 SSOT (單一事實來源)：** `report_enrichment_service.py` 使用了硬編碼的提示詞字串，而沒有使用集中管理的 `PromptKeys` 列舉。
2. **Telegram 服務例外吞噬：** `report_service.py` 將 `telegram_service.send_message` 包在 `try...except` 區塊中，卻沒有意識到 `httpx.HTTPError` 已被該服務內部攔截並回傳布林值 `False`。這導致了網路逾時被靜默吞噬。
3. **LLM Tier 3 無法使用 (營運成本攀升)：** `hybrid_router.py` 去檢查一個靜態、僅供診斷用的檔案 (`hardware_capability_matrix.json`) 來決定 Tier 3 (Ollama) 是否可用。因為該檔案在正式環境中並不存在，導致所有本應派發給 Tier 3 的查詢全部 fallback 到 Tier 1，造成營運成本增加。

## 需要使用者審查
無。這些變更嚴格遵循既有的系統架構（SSOT、DRY 與錯誤處理原則），並未引入任何新功能。

## 提議的變更

### 提示詞與 SSOT

#### [MODIFY] report_enrichment_service.py (file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_enrichment_service.py)
- 將 `prompt_key="nexus_oracle_agent"` 更改為使用 SSOT 列舉：`prompt_key=PromptKeys.NEXUS_ORACLE_AGENT_PROMPT.value`。
- 徹底移除硬編碼的 `fallback_prompt` 字串。`PromptService` 已經會透過 SSOT 預設值來處理 Fallback。

### 錯誤處理

#### [MODIFY] report_service.py (file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_service.py)
- 重構 `_create_summary_task_and_log`。不再忽略 `await telegram_service.send_message(...)` 的回傳值，而是明確檢查它是否回傳了 `False`（這代表內部發生了如 `httpx.HTTPError` 等失敗）。
- 移除包圍在 `send_message` 呼叫外圍無效的 `try...except Exception`，因為 Telegram 服務本身已經會捕捉它自己的例外。準確地記錄失敗日誌並標記任務。

### LLM 混合路由 (Hybrid Routing)

#### [MODIFY] hybrid_router.py (file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/llm/hybrid_router.py)
- 重構 `is_query_simple_and_offline`，改由從資料庫 SSOT (`SettingsService().get_setting("ollama_discovered_models")`) 取得本機 Ollama 模型的可用性，不再依賴靜態的 `hardware_capability_matrix.json`。
- 解析 JSON 設定，準確判斷 `qwen`、`gemma` 或其他設定好的本機模型是否確實存在，讓合法的簡單查詢能正確路由至 Tier 3。

## 驗證計畫

### 自動化測試
- 執行 `uv run pytest tests/services/test_report_service.py` 確保 Map-Reduce 報告邏輯不受影響。
- 執行 `uv run pytest tests/test_llm_fallback.py` 確保 Fallback 路由邏輯不受影響。

### 人工驗證
- 檢查 Hugging Face 伺服器日誌，確認 `hybrid_router` 成功將簡單離線查詢路由至 `Tier 3`，而非預設的 `Tier 1`。
- 確認 Telegram 通知在發生 Timeout 逾時時依然能優雅降級 (Graceful Degradation)，且不會導致報告週期崩潰。

> [!IMPORTANT]
> 指揮官，這是基於物理對帳後，最符合 Archon SSOT 與 DRY 架構的解決方案。請問是否批准我立刻開始修改這兩個檔案？

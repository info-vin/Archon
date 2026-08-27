# 實作計畫 - 降級 MockLLMClient 屬性缺失與無金鑰 Fail-Fast 防禦性硬化 (Phase 5.11.6)

解決當 API 金鑰解密失敗（或缺失）時，系統因「樂觀路徑」引發的兩個核心問題：
1.  **無金鑰靜默降級（樂觀路徑）**：在非測試環境（例如生產環境 HF Space）下，若無金鑰，系統原先會靜默降級使用 `MockLLMClient` 回傳 `✨ [Mock] Magic Content...` 假數據欺騙使用者與自癒程序。我們將修改為 **Fail-Fast 機制**：在非測試環境下若缺失金鑰，直接拋出 `ValueError` 以暴露真實的配置錯誤。
2.  **屬性缺失崩潰**：在測試環境下，當降級至 `MockLLMClient` 時，`DefaultLLMStrategy` 因為直接存取 `res_msg.tool_calls` 而引發 `AttributeError: 'MockMessage' object has no attribute 'tool_calls'` 崩潰。我們將使用 `getattr` 進行防禦性讀取。

## 使用者審查項目

> [!IMPORTANT]
> 1.  **Fail-Fast 硬化**：若在生產/本地開發環境下缺失 LLM 金鑰，系統將**直接報錯中斷**，不再使用 Mock 數據虛假運行。
> 2.  **安全讀取屬性**：將直接存取 `res_msg.tool_calls` 改為防禦性的 `getattr(res_msg, "tool_calls", None)`，此變更安全且向後相容。

## 預計變更

### 後端 - LLM 客戶端模組

#### [修改] [clients.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/llm/clients.py)

- 在 `get_llm_client` 的無金鑰 Fallback 區塊，讀取 `get_config().is_testing`：
  - 如果 **不是** 測試環境（`is_testing == False`），則直接拋出 `ValueError(f"CRITICAL: {provider_name.capitalize()} API key not found in environment or database.")`，拒絕虛假運行。
  - 只有在測試環境下，才允許降級至 `MockLLMClient`。

### 後端 - LLM 核心分發模組

#### [修改] [dispatcher.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/agents/dispatcher.py)

- 在 `DefaultLLMStrategy.execute` 中，使用 `getattr(res_msg, "tool_calls", None)` 安全讀取替代原本的直接屬性讀取。

## 驗證計畫

### 自動化測試
*   執行現有 Agent 整合與路由測試，確保無衰退 (No Regression)：
    ```bash
    uv run pytest tests/server/services/test_agent_service.py
    uv run pytest tests/services/test_agent_service_routing.py
    ```
*   新增單元測試：
    1.  驗證在 `is_testing = True` 時，`MockLLMClient` 的 `MockMessage` 屬性安全讀取不會引發 `AttributeError`。
    2.  驗證在 `is_testing = False` 時，若缺失 API 金鑰，呼叫 `get_llm_client` 會直接拋出 `ValueError`。

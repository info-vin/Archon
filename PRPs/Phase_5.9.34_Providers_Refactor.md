# Phase 5.9.34: Providers API SSOT 與 DRY 重構計畫

## 目標 (Goal)
解決 `python/src/server/api_routes/providers_api.py` 中存在的單一事實來源 (SSOT) 與「不重複造輪子 (DRY)」原則的違規問題。目前的 API 路由硬編碼了各家 LLM 供應商的 Base URL，並寫了大量重複的連線測試邏輯。我們將會把這些邏輯進行整併，並使其與 `python/src/server/services/credentials/provider_configs.py` 中的設定保持一致。

## 需要使用者的審查 (User Review Required)
> [!IMPORTANT]
> 針對 `providers_api` 的自動化測試，我們將會使用 `unittest.mock.patch` 來模擬 (Mock) `httpx.AsyncClient`，以確保在 CI 環境執行時不會發送任何真實的外部網路請求。請確認您是否同意採用這個 Mock 方案。

## 待確認問題 (Open Questions)
- **Ollama 測試需求 (已結案)**：經查閱 `git log -p -S"ollama"` 的歷史數據，`ollama` 雖然曾存在於 `allowed_providers` 名單中，但從未被實作於 `PROVIDER_TESTERS` 內，歷史存取只會回傳 400 Not Supported。基於此數據事實，我們將維持原狀，**不實作** Ollama 的連線測試。

## 預期修改內容 (Proposed Changes)

---
### 供應商設定 (Provider Configurations)
將所有供應商的對應關係與設定進行收攏，使其成為唯一的單一事實來源 (SSOT)。

#### [MODIFY] [provider_configs.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/credentials/provider_configs.py)
- 擴充 `_get_provider_api_key` 函式內的 `key_mapping`，補齊 `anthropic`、`openrouter` 與 `grok` 的 API Key 映射。
- 擴充 `_get_provider_base_url` 函式，使其能夠回傳所有 5 家供應商正確的 Base URL（從而拔除 API 路由內的硬編碼）。

---
### API 路由 (API Routes)
重構 Providers API 以落實 SSOT，並刪除所有重複的程式碼。

#### [MODIFY] [providers_api.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/api_routes/providers_api.py)
- 移除檔案內的 `PROVIDER_KEY_MAP`，改為完全依賴 `provider_configs.py` 或統一的設定管理。
- 刪除 5 個重複的連線測試函數（例如 `test_openai_connection`、`test_google_connection` 等）。
- 建立一個單一的泛型測試函數 `async def test_provider_connection(provider: str, api_key: str, base_url: str) -> bool`，用來動態處理不同供應商的 Headers 差異（例如 `Authorization: Bearer` vs `x-api-key` vs `x-goog-api-key`）。
- 在 `/{provider}/status` 的路由端點中，全面改用這個單一泛型測試函數。

---
### 階段稽核腳本 (Phase Audit Script - Quality Gate)
強化稽核腳本的規則，確保未來能自動攔截類似的硬編碼問題。

#### [MODIFY] [phase_audit.py](file:///Users/vincenta/GoogleKwok022/Archon/scripts/phase_audit.py)
- 更新 `url_pattern` 正規表達式，使其能夠抓出不帶有埠號 (`:port`) 的標準硬編碼網址。
- 更新 `set_literal_pattern`，加入對「陣列 (List)」字串的偵測，以攔截被用於 RBAC 權限判斷的陣列硬編碼（例如 `["admin", "manager"]`）。

---
### 自動化測試 (Automated Tests)
確保重構後的連線測試功能正常無誤。

#### [NEW] [test_providers_api_refactor.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/test_providers_api_refactor.py)
- 使用 `FastAPI` 的 `TestClient` 與 `pytest` 為 `/api/providers/{provider}/status` 路由撰寫單元測試。
- 模擬 (Mock) `httpx.AsyncClient.get` 的行為，測試各供應商回傳成功 (200) 以及失敗 (401/500) 時的連線反應。

## 驗證計畫 (Verification Plan)

### 自動化測試與程式碼品管 (Automated Tests & QA)
- 執行 `make lint` (及 `make lint-be`, `uv run mypy src/`) 確保修改後的程式碼符合 PEP8 與靜態型別安全，沒有語法斷層。
- 執行 `make test-be`，確保所有的連線測試邏輯行為與重構前完全一致，無任何 Regression。
- 執行 `make phase-audit`，確保新的稽核規則能在重構後的乾淨代碼上順利通過，並且能發揮防堵硬編碼的作用。

### 自動化日誌驗證 (Automated Log Verification)
- 啟動伺服器並發送測試請求至 `/api/providers/openai/status`。
- 自動抓取 Docker 日誌 (`docker compose logs --tail=50 archon-server`)，核實是否有正確印出連線測試成功 (`connectivity test result: True`) 的日誌，確保不依賴人工肉眼等待。

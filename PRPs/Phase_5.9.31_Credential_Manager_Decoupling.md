# Phase 5.9.31: Test Debt Decoupling & CredentialManager Purification

## 1. 緣起與目的 (Background & Purpose)
在 Phase 5.9.30 (Agent API Routing 拆分) 的過程中，我們成功將 LLM/Embedding 的邏輯分離到 `provider_configs.py`，但在拔除 `CredentialManager` 內舊有呼叫代理 (Proxy Wrappers) 時遇到了重大阻礙：**44 項以上的單元測試發生崩潰**。

**目的**：
我們不能容許系統內存在「虛假測試 (False Mocks)」。目前 `tests/` 底下有超過 6 個測試檔案、將近 40 處代碼仍然依賴 `mock_credential_service.get_active_provider`。這違反了軟體工程中的**單一職責原則 (SRP)**，因為 `CredentialManager` 理論上只應該管理資料庫中的 `archon_credentials` CRUD 操作，不應該知道 LLM 的路由。
Phase 5.9.31 的唯一目的就是**消除這筆測試技術債**，徹底根除 `manager.py` 的 God Object 特性。

此階段的核心是「絞殺榕模式 (Strangler Fig)」的最後一哩路：將所有的測試依賴遷移到 `provider_configs.py`，然後徹底拔除 `manager.py` 中的 5 個向下相容代理。

## 2. 影響範圍 (Impact Scope)
透過全域搜尋，確認至少有以下測試檔案受到影響，需要進行重構：
- `tests/integration/services/test_phase47_devbot_skills.py`
- `tests/server/services/test_agent_service.py`
- `tests/test_async_credential_service.py`
- `tests/test_async_llm_provider_service.py` (重災區)
- `tests/test_hybrid_routing.py`
- `tests/test_llm_fallback.py`

## 3. 實作計畫 (Implementation Plan)

### Step 1: 替換測試 Mock 標的 (慢慢修改)
- 我們將「慢慢修改」，分批次針對上述受影響的測試檔案進行替換，確保每一次修改都不會造成意料之外的破壞。
- 將上述測試檔案中所有 `patch.object(credential_service, "get_active_provider", ...)` 或 `mock_credential_service.get_active_provider` 的寫法，逐步替換為 Mock `src.server.services.credentials.provider_configs.get_active_provider`。
- 其他 4 個代理方法 (`get_embedding_provider_configs`, `check_credentials_exist`, `_get_provider_api_key`, `_get_provider_base_url`) 也依序分批在測試中改為 Mock `provider_configs.py` 內對應的函數。

### Step 2: 拔除代理與淨化 Manager
- 回到 `python/src/server/services/credentials/manager.py`。
- 將 `--- Backward Compatibility / Proxy Wrappers ---` 區塊下方的 5 個方法徹底刪除。
- 這樣 `manager.py` 就會成為純粹的 DB CRUD 元件，不再與 `provider_configs.py` 產生循環依賴或權責不清。

### Step 3: 驗證公證 (Verification)
- 執行 `make lint-be`，確保修改過程沒有引入任何型別錯誤 (mypy) 或是風格警告 (ruff)。
- 執行 `make test-be`，確保原本的 613 個測試依然能全數通過，且不再引發任何 `AttributeError`。
- 執行 `make phase-audit`，確認健康度無損傷。

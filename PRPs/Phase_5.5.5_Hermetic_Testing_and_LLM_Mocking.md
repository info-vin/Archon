# Phase 5.5.5: 密閉測試環境與大模型全局 Mock 實作計畫 (Hermetic Testing & LLM Mocking)

## 目標 (Objective)
建立 100% 離線可運行、不依賴外部網絡與大模型 API 密鑰的密閉測試環境 (Hermetic Testing)。徹底解決因 API 限流 (429)、網絡中斷或認證密鑰缺失導致的測試不穩定問題，保障 CI/CD 與 Agent 自我驗證效率。

---

## 規劃方案 (Three-Tier Strategy)

### 方案 1: 全局大模型 Mock 門禁 (Global LLM Mocking)
* **核心機制**:
  * 攔截 `openai.AsyncOpenAI`、`openai.OpenAI` 與 `google.genai.Client` 請求。
  * 針對 PydanticAI 的 Agent，全面引進 `pydantic_ai.models.test.TestModel` 進行測試期注入。
  * 提供確定性 (Deterministic) 的模擬回覆，保證單元測試 100% 本地化。

### 方案 2: 資料庫與 Supabase 網路請求攔截 (SQLite / Supabase Client Mock)
* **核心機制**:
  * 對 `get_supabase_client` 進行測試依賴注入 (Dependency Injection)。
  * 用 `respx` 攔截對 `*.supabase.co` 的所有 HTTP 調用，避免直連雲端。
  * （長期目標）建立記憶體內 (In-Memory) SQLite 數據儲存庫，模擬 CRUD 回應。

### 方案 3: 單元與集成測試徹底分離與斷網跳過 (Test Separation & Network Auto-Skip)
* **核心機制**:
  * 通過 pytest `conftest.py` 配置，在測試啟動時檢測網絡連線狀態與環境變數。
  * 若無網絡或缺少金鑰，自動跳過帶有 `@pytest.mark.integration` 的測試，不引發 Error 崩潰。

---

## 第一階段執行結論 (Stage 1 Conclusions)
* **執行狀態**：🟢 已完成並驗證通過。
* **交付產物**：
  * 實作了 [conftest.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/conftest.py) 全局 Mock 機制（Google GenAI, OpenAI, LiteLLM, PydanticAI Agent）與 pytest `pytest_runtest_setup` 自動 Skip 門禁。
  * 新增 [test_mock_sovereignty.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/test_mock_sovereignty.py) 驗證 Mock 機制的邊界主權與防護力。
  * 修正 `test_embedding_service_no_zeros.py` 以支援在全域 Mock 下正常拋出預期例外。
* **驗證數據**：
  * `make test-be-fast`：**581 測試全數通過**，5 項整合測試於斷網/無金鑰環境下安全跳過（Skipped）。
  * `make lint-be`：**All checks passed!**（344 個後端檔案無 Lint 錯誤與型別問題）。

---

## 第二階段執行結論 (Stage 2 Conclusions)
* **執行狀態**：🟢 已完成並驗證通過。
* **交付產物**：
  * 在 [conftest.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/conftest.py) 中引進了 `respx` 物理攔截器，成功阻斷所有未被 mock 攔截而直連 `*.supabase.co` 的 HTTPX 連線，丟出 `httpx.ConnectError`。
  * 實作了記憶體狀態化模擬客戶端 `StatefulMockSupabaseClient`（包含 `MockTable` 與 `MockQueryBuilder`），支援 `.eq()`, `.neq()`, `.ilike()`, `.contains()`, `.limit()` 等運算子鏈式調用，在單一測試期內完全模擬了增刪查改（CRUD）的一致性。
  * 新增 [test_supabase_stateful_mock.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/test_supabase_stateful_mock.py) 用以驗證狀態 CRUD 和 respx 阻斷率。
* **驗證數據**：
  * `make test-be-fast`：**579 測試全數通過**，9 項整合測試於斷網時安全優雅跳過（Skipped）。
  * `make lint-be`：**All checks passed!**（344 個後端檔案無 Lint 警告，符合 Ruff E402 標準）。

---

## 驗證計畫 (Verification Plan)

### 自動化測試 (Automated Tests)
```bash
# 1. 執行快軌測試驗證
make test-be-fast

# 2. 執行後端靜態類型與語法檢查
make lint-be
```

# Code Review: Test Hang Fix & Shadow DB Migration Sequence

此報告針對最新的提交 `66de4bbc` 進行代碼審查，主要檢視 `TestClient` 的重構、依賴隔離以及影子資料庫遷移腳本的順序調整。

## 1. 測試套件重構 (Test Suite Teardown & Isolation)

### 1.1 `yield TestClient(app)` 取代 Context Manager
* **變更檔案:** `test_settings_api.py`, `test_marketing_api_list_leads.py`, `test_marketing_api_draft_from_leads.py`
* **審查意見 (Code Review):**
    * ✅ **優點:** 原本使用 `with TestClient(app)` 會觸發 FastAPI 的 `startup` 和 `shutdown` lifespan 事件，這對於只需單元測試的小型端點而言是多餘的，更會啟動排程器 (Scheduler) 等背景服務，導致測試卡死。改用 `yield TestClient(app)` 直接產生實例而不進入 Context Manager，是非常精準的改動，從根本上杜絕了副作用。
    * ✅ **優點:** 將 `client` 從全域變數改為 `pytest.fixture`，確保每個測試都能獲得乾淨的實例。

### 1.2 `dependency_overrides` 的外科手術式清理
* **變更檔案:** `test_settings_api.py`, `test_marketing_api_list_leads.py`
* **審查意見 (Code Review):**
    * ✅ **優點:** 移除了粗暴的 `app.dependency_overrides.clear()`，改為使用 `app.dependency_overrides.pop(get_current_user, None)`。這保證了只會移除特定測試所掛載的 Mock 依賴，不會意外清空系統中其他必要的全域依賴設定，這符合高聚合、低耦合的設計原則 (SSOT)。

### 1.3 `patch` 範圍縮小與實例化
* **變更檔案:** `test_marketing_api_draft_from_leads.py`
* **審查意見 (Code Review):**
    * ✅ **優點:** 將原本直接 patch 靜態方法 `MarketingService.draft_from_leads` 的作法，改為 patch 整個 `MarketingService` 類別，再對回傳的 instance 方法做 `AsyncMock`。這樣更符合 Python 類別實例的測試模式，防止未來方法簽章改變時的報錯。

---

## 2. 資料庫遷移順序重構 (Shadow DB Migration)

### 2.1 Schema 宣告提早 (05 -> 02)
* **變更檔案:** `migration/0.2.3/02_schema_features.sql`, `migration/0.2.3/05_seed_system_configs.sql`
* **審查意見 (Code Review):**
    * ✅ **優點:** 徹底解決了 `relation "public.archon_roles_permissions" does not exist` 的嚴重錯誤。將資料表結構 (`CREATE TABLE`) 嚴格放在第 2 階段 (`02_schema_features.sql`)，讓 RLS 安全原則 (第 4 階段) 有實體對象可綁定，而種子資料 (`INSERT`) 維持在第 5 階段。這是物理對齊的標準範例。

### 2.2 殘留與錯位的 ALTER 語法 (01 -> 02)
* **變更檔案:** `migration/0.2.3/01_schema_core.sql` (移除), `migration/0.2.3/02_schema_features.sql` (新增)
* **審查意見 (Code Review):**
    * ✅ **優點:** 先前某次重構不小心將 `archon_prompts` 的 ALTER 語法塞進了 `01_schema_core.sql` (此時表還未建立)。將其搬移到 `02_schema_features.sql` 最末端，確保實體存在後才進行 metadata 的 JSONB 更新。

---

## 3. 基礎設施腳本 (Infrastructure Scripts)

### 3.1 移除硬編碼的 Fallback
* **變更檔案:** `scripts/archive/verify_system.py`, `scripts/init_db.py`
* **審查意見 (Code Review):**
    * ✅ **優點:** 將硬編碼的 `"0.2.2"` Fallback 更新為現行的 `"0.2.3"`。這確保了在資料夾匹配失敗或特定極端環境下，腳本仍能 fallback 到正確的最新版本目錄。
    * ⚠️ **建議 (未來改進):** 雖然已更新 fallback，但更佳的做法應該是讓腳本自動抓取 `migration/` 下最大版號的資料夾，而完全不依賴字串 hardcoding。但目前的 `init_db.py` 已經實作了動態抓取邏輯，fallback 只作為保險絲，因此現狀可接受。

---

## 4. 總結 (Summary)
**審核結果：通過 (Approved)**

本次提交（`66de4bbc`）是一次高水準的技術債清理與維運修復。程式碼完全遵循了 DRY 與 SSOT 精神。尤其是對 FastAPI `TestClient` Context Manager 副作用的認知與處理，展現了對底層框架生命週期的深刻理解。無任何安全隱患或架構破壞。

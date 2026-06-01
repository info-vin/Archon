# Phase 5.5.4: 提示詞統一治理重構計畫 (Prompt Governance Integration Plan)

## 目標 (Objective)
消除後端服務與 API 中分散且寫死 (Hardcoded) 的 Prompt 字串，將其統一納入 `prompt_service` 管理。此舉可落實「Prompt SSOT (單一事實來源)」，使所有系統 Prompt 均能從資料庫中動態讀取與調整，並支持 Traditional Chinese (繁體中文) 語系約束。

---

## 背景與發現 (Background)
根據代碼審查，目前系統中有 8 個關鍵業務服務在調用大語言模型 (LLM) 時，直接將 System Prompt 寫死在代碼中，繞過了 `prompt_service` 的統一治理機制。

### 待重構之硬編碼服務清單：
1. **`contextual_embedding_service.py`** (RAG 脈絡化嵌入服務)
2. **`extraction_service.py`** (網頁資訊提取)
3. **`job_board_service.py`** (業務求職分析)
4. **`business_archiver.py`** (行銷風格審計)
5. **`approval_manager.py`** (經理審批建議)
6. **`ai_operations.py`** (專案經理與助理運算)
7. **`ai_metadata.py`** (爬蟲元數據與標題生成)
8. **`summarization.py`** (程式碼範例摘要分析)
9. **`audio_api.py`** (經理語音簡報生成)

---

## 執行計畫 (Execution Plan)

### 1. 資料庫 Prompt 種子資料擴充 (Database Seeding)
在資料庫種子檔案中新增對應的 Prompt 鍵值，確保重構後的系統有默認的資料庫紀錄。
* **新增鍵值 (Prompt Keys)**:
  * `EMBED_CONTEXT_GENERATOR`: 脈絡化嵌入 System Prompt。
  * `DATA_EXTRACTION_EXPERT`: 網頁數據結構化提取 System Prompt。
  * `SALES_ASSISTANT_JOB_BOARD`: 求職看板分析助手 System Prompt。
  * `AI_STYLE_AUDITOR`: 經理審查風格稽核 System Prompt。
  * `MARKETING_DIRECTOR_REVIEW`: 行銷草稿審批推薦 System Prompt。
  * `PROJECT_OWNER_ASSISTANT_PO`: 專案經理 POBot System Prompt。
  * `CHARLIE_ASSISTANT_PM`: Charlie 經理助理 System Prompt。
  * `SOURCE_METADATA_SUMMARY`: 爬蟲資源庫元數據總結 System Prompt。
  * `SOURCE_TITLE_GENERATOR`: 爬蟲資源庫標題生成 System Prompt。
  * `CODE_EXAMPES_AUDITOR`: 代碼範例分析 System Prompt。
  * `CHIEF_OF_STAFF_AUDIO_BRIEFING`: 語音簡報幕僚 System Prompt。

### 2. 服務層代碼重構 (Service Layer Refactoring)
* 將上述檔案中的寫死字串移出，改為調用 `prompt_service.get_prompt(key, default)`，確保在資料庫讀取失敗時，能安全回退至代碼中的 default 提示詞。
* **範例**:
  ```python
  # 重構前
  system_prompt = "You are a Data Extraction Expert..."
  
  # 重構後
  from src.server.services.prompt_service import prompt_service
  system_prompt = prompt_service.get_prompt("DATA_EXTRACTION_EXPERT", default_prompt)
  ```

### 3. 測試與驗證 (Verification)
* 執行 `make lint-be` 確保引入與語法無誤。
* 執行 `make test-be` 驗證所有 Agent 整合測試與 API 測試在重構後仍能全數通過。

---

## 驗證結果與變更紀錄 (Walkthrough)

本階段提示詞統一治理重構已於 2026-06-01 順利完成並結案。

### 1. 提示詞服務整合
* **脈絡化嵌入與網頁數據提取**：在 `contextual_embedding_service.py` 與 `extraction_service.py` 中，成功移除了寫死的 String 字串。脈絡嵌入現在動態查閱 `EMBED_CONTEXT_GENERATOR`；結構化網頁數據提取則從 `DATA_EXTRACTION_EXPERT` 動態獲取格式化範本，利用 Python `.format(schema_json=...)` 動態渲染 JSON 格式規範。
* **Agent 系統指令動態化**：重構了 `business_archiver.py`、`ai_operations.py`、`ai_metadata.py`、`summarization.py`、與 `audio_api.py`。包含 POBot、助理 PM 以及語音音訊等模組均全部對齊 `prompt_service.get_prompt` 入口。

### 2. 靜態與品質門禁驗證
* 執行 `make lint-be` 後端靜態檢查，全專案 344 個 Python 檔案 **100% 通過 (All checks passed)**，無任何語法錯誤、動態導入失效或循環依賴問題。

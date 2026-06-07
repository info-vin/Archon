name: "Phase 5.5.9 - 3-Tier Multi-Agent Fallback Architecture with Human Control (具備人機協作控制的三層容災降階架構)"
status: "🟢 已完成 (Completed - 2026/06/07)"
description: |
  實作健壯的三層模型降階路由機制（Gemini -> Hugging Face -> 本地 Ollama），並整合明確的人類監督機制，包含前端 5173 (enduser-ui-fe) 設定介面控制與實時連線狀態顯示。

---

## 1. 目標與背景 (Goal & Context)

**背景**: 
基於我們 2026 年 5 月在 `OFFLINE_MODE` 雙軌架構中的開發經驗，系統必須具備在極端環境下生存的能力。目前，如果主要的雲端模型（例如 Google Gemini）因信用額度耗盡或缺乏 API Key 失敗，系統會直接降階到本地的 Ollama。

**問題**: 
直接降階到本地模型會立即對本地的 CPU/記憶體造成巨大壓力。Hugging Face Spaces 提供了免費的 Serverless 推理 API，但我們必須僅將其作為**運算 API 降階備援 (Tier 2)**，而非儲存後端。
更重要的是，從**人機協作 (Human-Agent Collaboration)** 的角度來看，靜默的降階會使人類開發者無法感知模型品質下降或本地硬體超載，因此人類操作者需要具備清晰的透明度與覆寫控制權。

**解決方案**: 
我們將 Hugging Face 整合為**運算降階備援 (Tier 2)**。為了符合人機協作目標，我們將實作：
1. **狀態透明化**: 在 UI 介面設計實時狀態標籤（Status Badge），顯示當前作用中的模型層級。
2. **人類覆寫控制**: 在 **5173 (enduser-ui-fe)** 設定面板提供 `HF_TOKEN` 輸入框，並允許手動強制指定特定 Tier 以便進行測試與除錯。

---

## 2. 具備人機協作控制的三層降階架構

| 層級 (Tier) | 執行環境 | 提供商 | 觸發條件 | 架構特徵 | 人類可見度 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | 主要雲端 | Google Gemini / OpenAI | 預設 | 高精度、高速度。 | 已連線 (綠色燈號) |
| **Tier 2** | 次要雲端 | Hugging Face Free API | `AuthenticationError` (無額度/無Key), `RateLimitError` (429/503) | 減輕本地硬體負擔。需要網路與 `HF_TOKEN`。 | 降階警示 (黃色閃爍) |
| **Tier 3** | 極端本地 | Ollama (Gemma3) | `ConnectionError` (斷網) 或 Tier 2 失敗 | 觸發 `OFFLINE_MODE`。降階至 384 維向量。零外部依賴。 | 本地離線模式 (橘色燈號) |

---

## 3. 實作步驟 (Implementation Steps)

### 步驟 3.1: 憑證與後端設定擴充
**目標檔案**: [credential_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/credential_service.py) 以及 RAG 設定相關 API 端點。
- 擴充憑證服務以安全地獲取、驗證與快取 `HF_TOKEN`。
- 新增後端設定欄位 `forced_fallback_tier`（可選值：`null`, `1`, `2`, `3`）以支援人類手動覆寫。
- 提供系統狀態 API 端點，回傳 `{"active_tier": 1 | 2 | 3, "internet_connected": bool}`。

### 步驟 3.2: 提供商註冊與模型映射
**目標檔案**: `python/src/server/services/llm/utils.py` 與 `python/src/server/services/llm/models.py`
- 將 `"huggingface"` 註冊為合法的模型提供商。
- 實作模型映射表，將內部 Prompt 請求轉換為 HF Hub 模型 ID（例如將快速對話映射至 `google/gemma-1.1-2b-it`，將向量映射至 `sentence-transformers/all-MiniLM-L6-v2`）。

### 步驟 3.3: 具備覆寫功能的 3-Tier 路由邏輯
**目標檔案**: `python/src/server/services/llm/clients.py`
- 修改 `get_llm_client` 以優先尊重人類設定的 `forced_fallback_tier`。
- 實作級聯路由：
  - 嘗試 **Tier 1**（預設）。
  - 若 `forced_fallback_tier == 2` 或 Tier 1 觸發認證/頻率限制錯誤（且網路正常），則降階至 **Tier 2**（透過 OpenAI 相容客戶端連接 Hugging Face）。
  - 若 `forced_fallback_tier == 3`、網路中斷（`ConnectionError`）或 Tier 2 執行失敗，則降階至 **Tier 3**（本地 Ollama）。

### 步驟 3.4: 前端設定面板與 Token 輸入
**目標檔案**: **5173 前端面板**相關組件
- 在設定面板的 RAG 提供商網格中新增 "Hugging Face Fallback" 區塊，供安全輸入 `HF_TOKEN`。
- **`HF_TOKEN` 取得方式**：
  1. 登入 Hugging Face 帳號。
  2. 前往 [Hugging Face Settings -> Access Tokens](https://huggingface.co/settings/tokens)。
  3. 點擊 **"New token"**，Token 角色選擇 **"Read"**（Serverless 推理僅需讀取權限即可），生成後複製輸入。
- **使用限制與警示**：
  - **速率限制 (Rate Limits)**：免費 Serverless Inference API 共享叢集流量，通常限制在每分鐘數千個 Token 或每秒數次請求。若超出限制，HF 會回傳 HTTP `429 Too Many Requests` 或 `503 Service Unavailable`，此時系統會自動無縫降階至 **Tier 3 (本地 Ollama)**。
  - **冷啟動 (Cold Start)**：若請求的模型目前在 Hugging Face 叢集中處於閒置狀態，首次請求可能需要 10~30 秒進行冷啟動載入，期間前端會有載入動畫提示。
- 提供單選按鈕/下拉選單，供使用者選擇「路由策略」：
  - `自動容災 (預設)`
  - `強制主要雲端 (Tier 1)`
  - `強制 HF 雲端運算 (Tier 2)`
  - `強制本地離線 Ollama (Tier 3)`

### 步驟 3.5: 實時降階狀態指示燈
**目標檔案**: **5173 前端面板** 頂欄 (Dashboard Header) 或導航狀態列。
- 建立狀態標籤組件 `<FallbackStatusBadge />`，透過輪詢狀態 API 獲取當前運作層級。
- 渲染狀態樣式：
  - `Tier 1`: 綠色 Tron 風格標籤（`主要雲端已連線`）。
  - `Tier 2`: 黃色脈衝霓虹標籤（`HF 降階備援作用中`）。
  - `Tier 3`: 橘色工業風格標籤（`本地離線模式`）。

### 步驟 3.6: 品質門禁與 E2E 驗證
- **單元測試**: Mock `httpx` 以觸發 HTTP 429/401 錯誤，驗證降階級聯順序。
- **手動驗證**: 透過新版設定 UI 強制指定 Tier 2 與 Tier 3，觀察狀態指示燈更新，並監控終端機中 Ollama 的 CPU 負載以確認路由精準度。
- 執行 `make test-be` 與 `make audit-qa` 確保管道零退化。

---

## 4. 驗收與實作狀態 (Implementation & Acceptance Status)

本階段已於 2026 年 6 月 7 日 100% 物理開發完成，並通過全方位測試與品質公證。

### 實作變更檔案清單
1. **資料庫自動種子設定**：
   - [init_db.py](file:///Users/vincenta/GoogleKwok022/Archon/scripts/init_db.py) 整合 `HF_TOKEN` 與 `forced_fallback_tier` 預設。
2. **後端憑證服務與狀態 API**：
   - [manager.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/credentials/manager.py) 提供層級跟蹤。
   - [system_api.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/api_routes/system_api.py) 提供 `/api/system/fallback/status` 並進行 socket DNS 檢測。
3. **客戶端生成與白名單**：
   - [utils.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/llm/utils.py) 註冊 `"huggingface"` 提供商。
   - [clients.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/llm/clients.py) 生成 HF OpenAI 相容客戶端。
4. **降階路由與自癒核心**：
   - [base.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/llm/base.py) 處理級聯降階、自癒重置與人類強制覆寫。
5. **前端管理設定與狀態指示燈**：
   - [FallbackStatusBadge.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/components/FallbackStatusBadge.tsx) 建立狀態狀態列並掛載。
   - [AdminFallbackConfig.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/features/admin/components/AdminFallbackConfig.tsx) & [AdminPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/AdminPage.tsx) 5173端 Fallback 設定。
   - [AdminSystemConfig.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/features/admin/components/AdminSystemConfig.tsx) 避免設定欄位重複呈現。
   - [index.tsx](file:///Users/vincenta/GoogleKwok022/Archon/archon-ui-main/src/features/rag-settings/index.tsx) & [types.ts](file:///Users/vincenta/GoogleKwok022/Archon/archon-ui-main/src/features/rag-settings/types.ts) & [credentialsService.ts](file:///Users/vincenta/GoogleKwok022/Archon/archon-ui-main/src/services/credentialsService.ts) 3737端 RAG 備援折疊面板。
6. **自動化測試**：
   - [test_llm_fallback.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/test_llm_fallback.py) 驗證全路由降階分支。

### 驗證通過狀態
* **單元測試 (`test_llm_fallback.py`)**：`4 passed` (0.35s)
* **全系統品質公證 (`make audit-qa`)**：`ALL GATEWAYS PASSED SUCCESSFULLY! 🟢`
* **數位雙生一致性對帳 (`make twin-scout`)**：`100% 物理對齊，零誤差`
* **靜態代碼與強型別檢測 (`make lint`)**：`Success: no issues found in 347 source files 🟢`

# Phase 5.10.12 Crawler Fallback Mechanism (爬蟲未達標保底機制)

## 背景與問題描述
目前 `JobBoardService.auto_fetch_daily_leads()` 的排程邏輯中，系統會依序爬取設定好的 `CRAWLER_JOB_KEYWORDS` (如 Python, AI 等 5 個類別)，每個類別最多抓取 `CRAWLER_JOB_LIMIT` (32) 筆資料。
**問題在於**：當潛在名單全部被 RAG 相似度閾值 (0.68) 或 LLM Judge 過濾淘汰時，最終入庫數量為 0。目前的迴圈機制在爬完一輪 (第一頁) 後會直接結束，導致當日完全沒有產生新的 Leads 與日報。

## 解決方案：未達標自動翻頁重爬 (Fallback Mechanism)
在不改變現有資料庫設定與嚴格過濾標準的前提下，於核心爬蟲邏輯中加入「自動翻頁 (Pagination) 保底」機制。

### 核心設計與約束 (SSOT & 零硬編碼)
1. **SSOT 全域設定 (Zero Hardcoding)**：拒絕在代碼中硬編碼 `max_pages=3`。我們將在 `CrawlerJobConfig` 中新增 `CRAWLER_MAX_PAGES` 欄位，確保翻頁上限完全由資料庫 (Settings) 動態控管。
2. **條件跳出 (Early Exit)**：只要在當前頁面循環結束後，`total_new_leads > 0` (有任一名單成功入庫)，就立即中斷翻頁，回報成功並結束排程，符合 DRY 原則。
3. **實體參數連動**：需將 `page` 參數一路打穿至最底層的 `_fetch_from_104_sync`。

## 具體修改計畫 (Implementation Plan)

### 1. 修改設定檔模型 (貫徹 SSOT)
**檔案:** `python/src/server/schemas/settings.py`
*   在 `CrawlerJobConfig` 中新增：
    `crawler_max_pages: int = Field(default=3, alias="CRAWLER_MAX_PAGES")`

### 2. 修改底層 Crawler 客戶端
**檔案:** `python/src/server/services/crawling/clients/job104_client.py`
*   修改 `search_jobs` 方法簽名，加入 `page: int = 1` 參數。
*   將 `page` 參數傳遞至 `self._fetch_from_104_sync(session, keyword, limit, page)`。
*   在 HTTP params 中將寫死的 `"page": "1"` 替換為 `"page": str(page)`。

### 3. 修改介面層與中介層
**檔案:** `python/src/server/api_routes/marketing_api.py`
**檔案:** `python/src/server/services/marketing_service.py`
*   同步修改這兩處的 `search_jobs` 定義，加入 `page: int = 1` 預設參數以確保簽名 100% 相容。

### 4. 修改排程任務主邏輯 (保底翻頁機制)
**檔案:** `python/src/server/services/job_board_service.py`
*   修改 `search_jobs` 加入 `page: int = 1`。
*   修改 `auto_fetch_daily_leads`，加入外層翻頁迴圈，並嚴格讀取 SSOT 配置：
    ```python
    max_pages = config.crawler_max_pages  # 從 SSOT 讀取，絕不硬編碼
    blocked = False
    for page in range(1, max_pages + 1):
        for keyword in keywords:
            # 傳遞 page 參數
            jobs = await self.search_jobs(keyword, limit=limit, client=session, page=page)
            # ... 省略過濾與存檔 ...
            # 遇 WAF 阻擋則 break
        
        if blocked:
            break
            
        # 只要有一筆成功，立即跳出
        if total_new_leads > 0:
            logger.info(f"Successfully fetched {total_new_leads} new leads.")
            break
    ```

## 嚴格驗證計畫 (No Fake Validation)
1. **防禦改 A 壞 B (單元測試公證)**：
   - 將修改或新增 `tests/` 內的測試，使用 mock 驗證「當第一頁回傳 0 筆時，是否正確呼叫第二頁」以及「讀取 `crawler_max_pages` 的 SSOT 行為」。
   - 執行全局 `make test-be` 確保無任何破壞性變更 (Backward Compatibility)。
2. **實體穿透測試**：
   - 手動觸發一次 `auto_fetch_daily_leads`，透過觀察日誌 (Log) 確認 HTTP 請求的 `page` 參數是否如預期從 1 遞增至 2。

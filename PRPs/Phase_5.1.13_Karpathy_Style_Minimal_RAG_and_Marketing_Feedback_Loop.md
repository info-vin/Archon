# Phase 5.1.13: Karpathy 式極簡 AI 知識庫與行銷反饋閉環實作計畫

本計畫旨在將 Bob 的內容工作臺與系統 RAG 知識庫進行優化，以符合 Andrej Karpathy 的極簡 AI 知識庫哲學：**「輕量化視覺、重度原始輸入、強大負面反饋閉環」**。

---

## 預期修改內容

我們將實作以下三個核心模組，以加固此架構：

### 1. 實用主義視覺與圖表（零 Token 穩定度）
確保所有 UI 圖表皆由前端本地渲染，且 AI 視覺生成能優雅地降級為本地幾何 SVG，以保護我們的 API Token 額度。

#### [修改] [logo_tool.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/marketing/logo_tool.py)
* 優化本地 SVG 生成器，使其能根據種子文字關鍵字，產生更多樣化的 Cyberpunk 與科技風格幾何圖樣。
* 確保生成的 SVG 格式正確，能直接在前端作為部落格文章的封面圖片。

#### [修改] [content_handler.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/marketing/content_handler.py)
* 優化 `generate_visual_asset`，當 `IMAGE_GEN` 設定缺失或遇到 API 限流 (429) 時，自動且快速地繞過雲端 Imagen 圖像生成。
* 確保其直接回傳本地幾何 SVG 或高品質靜態佔位圖（Picsum），實現零 API 成本消耗。

---

### 2. 「只管丟」的原始 URL 爬網輸入（Librarian 獵人模式）
讓 Bob 能在前端快速將原始素材餵給 RAG 系統，並於背景自動執行爬網與向量化。

#### [新增] [MarketingIngestion.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/features/marketing/components/MarketingIngestion.tsx)
* 在 Bob 的工作臺上建立一個精美簡單的 UI 組件，供其直接貼入網頁 URL（例如行業部落格、趨勢報告）。
* 當輸入 URL 時，觸發 `/api/knowledge/crawl` 請求並帶入 `knowledge_type="marketing"`，於背景自動完成網頁抓取、切片與 Embedding 向量寫入。

#### [修改] [BrandWorkbenchView.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/features/marketing/components/BrandWorkbenchView.tsx)
* 將 `MarketingIngestion` 組件嵌入 Bob 的內容工作臺面板中，讓原始資料收集更直覺。

---

### 3. 風格自我修復與審查反饋閉環（風格編譯器）
強化經理審查與退件的反饋機制，使下一次生成的草稿自動優化。

#### [修改] [content_handler.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/marketing/content_handler.py)
* 審查 `process_approval` 機制，確保當經理駁回部落格文章時，系統能異步觸發 `LibrarianService().archive_style_critique`。
* 審查 `_get_expert_style_context` 邏輯，確保在 MarketBot 撰寫新草稿時，系統會調用 `LibrarianService().get_style_constraints(category="marketing")` 撈取這些動態提取的品牌限制條件，並自動注入 AI 系統 Prompt 中。

---

### 4. 測試環境隔離與 API 限流保護（自癒機制）
為了解決測試「昨天可以，現在壞了」的環境落差，我們必須加固前端與後端的測試防線：

#### [NEW] [env.test](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/.env.test)
* 新增前端獨立測試環境變數，將 `SUPABASE_URL` 與 `VITE_SUPABASE_URL` 導向虛擬的模擬網址 `https://test-isolated-physical-safety.supabase.co`，阻止測試發送真實 API 到雲端 Supabase。

#### [MODIFY] [gitignore](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/.gitignore)
* 加入 `.env`, `.env.test`, `.env.local`, `.env.test.local` 到忽略名單，確保測試設定檔不會被誤 commit。

#### [MODIFY] [vite.config.ts](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/vite.config.ts)
* 於 `test` 區塊下新增 `testTimeout: 10000`，放寬單元測試超時門檻，抵禦 jsdom 載入過慢。

#### [MODIFY] [test_phase53_workflow.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/integration/test_phase53_workflow.py)
* 新增檢查 `RUN_INTEGRATION_TESTS` 環境變數。除非設為 `"true"`，否則本地 `make test-be` 將自動跳過此打真實 Gemini API 的整合工作流測試，避免因 API 503 封鎖整個測試。

---

## 驗收與驗證計畫

### 自動化測試 & 雙生對帳巡航
* **雙生對帳巡航 (Twin Scout Audit)**：使用以下指令運行容器化 audit，確保後端 API 路由與前端頁面路徑 100% 物理對齊，且沒有任何路由斷層或未授權錯誤：
  ```bash
  make twin-scout
  ```
* **後端單元測試**：運行後端 Librarian 與行銷服務單元測試，驗證風格限制條件的存取：
  ```bash
  uv run pytest tests/test_marketing_essentials.py
  ```
* **前端單元測試**：運行前端測試，確保 Sankey 與 Funnel 圖表能正常以靜態 JSON 數據驅動渲染：
  ```bash
  npm run test src/features/marketing
  ```

### 手動驗證流程
1. 使用瀏覽器開啟 Bob 的行銷工作臺（連接至 Port `5173`）。
2. 在「原始素材匯入」框中貼入網頁 URL，並確認後端背景爬蟲已成功啟動並寫入向量庫。
3. 模擬經理 Charlie 駁回一個部落格草稿，並寫入特定修改意見（例如：「請多使用清單條列，並著重於零售業應用」）。
4. 要求 MarketBot 產生一篇新草稿，並在後端日誌中檢查提取出的風格限制是否已成功注入 LLM System Prompt。
5. 驗證文章封面配圖在雲端 API 無法使用時，能瞬間保底渲染為 Tron 風格的 SVG 幾何圖樣。

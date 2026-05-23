# Phase 5.3.0: 數位孿生錄影與知識庫行銷素材聯動計畫 (Dual-Purpose Marketing Pipeline)

## 📋 核心願景
為推廣「人機協作系統」，本計畫將行銷素材影片拆分為三向聯動的鏈路，打通自動化生成與側錄管道：
1. **行銷概念影片（頭與尾 - Intro/Outro）**：模擬登入 `gemini.google.com` 丟 Prompt 自動生成 4 秒「玫瑰開花」的高質感概念片。
2. **實機操作 Demo（身 - Body）**：側錄我們自己本地系統在跑 QA 驗收巡航時的人機協同對話與派單流程（基於 `twin_scout.py`）。

這些錄影資產將自動後處理並透過 Librarian 知識庫架構轉化為行銷資產，直接與 Marketing Persona (Bob) 的行銷工作台聯動，供其隨時調用與預覽。

---

## 🔍 技術標準與邊界限制
1. **互動式自癒登入 (Headed Auth Bypass)**：
   外部生成腳本預設開啟 Headed 模式，若偵測到 Google 帳號 Session 過期，會在終端機提示並等待 3 分鐘供使用者手動登入，隨後自動點擊「新對話/New Chat」以確保開啟全新 session。
2. **自動化下載監聽 (Auto-download Event)**：
   使用 Playwright 的 `page.expect_download()` 自動監聽下載行為，影片生成後自動完成下載並儲存至前端公開目錄，免除任何人工下載的摩擦。
3. **儲存代謝機制**：
   本地錄製的隨機 WebM 暫存檔會在轉檔完成後自動清理，僅保留轉換後的 MP4 素材，防止硬碟空間耗盡。
4. **前端播放器合規 (UI_STANDARDS.md 合規)**：
   * **Tailwind v4**：使用靜態類別配置播放器樣式，杜絕動態類別拼接。
   * **無障礙性 ARIA**：為播放按鈕與 RAG 引用 Popover 加上 `aria-label`、`aria-pressed` 及 `aria-expanded`。
   * **佈局安全**：在 flex 佈局下，為側邊欄外層容器配備 `min-w-0` 防止頁面被撐開。

---

## 🛠️ 具體實作步驟 (Actionable Plan)

### 第一步：外部素材自動生成與下載 (Intro/Outro)
*   **目標檔案**: `scripts/generate_gemini_intro.py` [NEW]
*   **實作細節**:
    *   載入 `.browser_data` 設定檔以重用 session。
    *   偵測登入按鈕，必要時等待 3 分鐘供手動登入。登入後點擊「新對話」按鈕。
    *   自動填入 Prompt `"可以製作4 秒 玫瑰開花的漫畫?"` 並 Enter 提交。
    *   藉由 while 迴圈輪詢偵測下載按鈕，觸發點擊後使用 Playwright 下載監聽器將影片保存至 `enduser-ui-fe/public/assets/videos/auto_demos/gemini_intro.mp4`。

### 第二步：Playwright 本地錄影機制注入 (Body)
*   **目標檔案**: `scripts/twin_scout.py` [MODIFY]
*   **實作細節**:
    *   在建立 `async_playwright` 的 `browser.new_context` 時，根據 `--record true` 參數掛載 `record_video_dir` 與 `record_video_size`。
    *   僅在驗收結果為 `WORKFLOW_SUCCESS` (綠燈) 時，保留影片並呼叫轉檔腳本；否則將暫存影片刪除。

### 第三步：自動化後處理與轉檔
*   **目標檔案**: `scripts/process_marketing_video.py` [NEW]
*   **實作細節**:
    *   呼叫 `ffmpeg` 將 Playwright 本地錄製的隨機 `.webm` 格式轉換為通用相容的 `marketing_demo.mp4`，存入前端 `auto_demos/` 目錄。
    *   在同目錄下產生伴隨描述檔 `marketing_demo.txt`（詳述操作場景，供 RAG 語義索引）。
    *   自動清理 `.webm` 暫存檔，並調用 `seed_knowledge.py` 重新為新影片進行索引。

### 第四步：Librarian 知識庫語義 Seeding
*   **目標檔案**: `scripts/seed_knowledge.py` [MODIFY]
*   **實作細節**:
    *   支援影片檔案（`.mp4`/`.webm`）的掃描與歸檔。當偵測到影片時，讀取其伴隨的同名 `.txt` 檔案作為 metadata，並以 `knowledge_type="marketing"` 導入 RAG 資料庫。
    *   自動偵測並跳過 companion `.txt` 的重複入庫。

### 第五步：前端 UI 影片播放整合
*   **目標檔案**: 
    - `EditorBody.tsx` (行銷編輯器 workbench) [MODIFY]
    - `RAGCitation.tsx` (RAG 引用彈窗) [MODIFY]
    - `SourceContextPane.tsx` (側邊欄 Context 卡片) [MODIFY]
*   **實作細節**:
    - 在 `EditorBody.tsx` 的 Preview 區塊檢測到影片格式時，自動將 `<img>` 替換為 HTML5 `<video>` 播放器（靜音、自動播放、循環）。
    - 在 `RAGCitation.tsx` 的 Popover 中，若 `citation.url` 為影片，直接內嵌小型 video 播放器，並加上 A11y 鍵盤屬性。
    - 在 `SourceContextPane.tsx` 中為影片卡片內嵌小型播放器，並為 `ExternalLinkIcon` 加上外部跳轉 <a> 連結。

### 第六步：整合 Makefile 指令
*   **目標檔案**: `Makefile` [MODIFY]
*   **實作細節**:
    *   新增 `make generate-marketing-intro` 以一鍵生成並自動下載外部概念影片。
    *   新增 `make twin-scout-marketing` 以一鍵啟動本地側錄並寫入 RAG 知識庫。

---

## ⚠️ 前置風險評估 (Pre-Action Assessment)
1. **FFmpeg 依賴**：需確保宿主機環境已安裝 `ffmpeg`，腳本應具備 Fallback 機制（若無安裝則至少複製原始 WebM 到同目錄並發出警告）。
2. **Google 帳號限流與驗證**：若 Google 二步驟驗證頻繁彈出，腳本會處於等待狀態，為此我們提供了最長 3 分鐘的互動式登入機制，以大幅提高自癒容錯能力。
# Phase 5.6.6 - Web UI Health Check & Synthetic Monitoring

## 🎯 核心目標 (Goal)
建立一個基於 **GitHub Actions** 的輕量級自動化監控機制，定時「戳 (Ping)」部署在 Vercel 上的 Web UI (Admin 與 End-user 雙前端)，確保網頁服務持續存活，並在發生 HTTP 400/500 等嚴重錯誤時，能第一時間發出警報，取代對外部第三方服務（如 cron-job.org）的依賴。

## 📋 實作步驟 (Implementation Plan)

### Phase 1: 輕量級 HTTP 狀態碼探測 (cURL-based Health Check)
1. **建立 Workflow 檔案**：在專案中建立 `.github/workflows/ui-health-check.yml`。
2. **設定排程 (Cron)**：設定 GitHub Actions 定時執行（例如每小時或每半小時執行一次）。
3. **撰寫探測腳本**：使用 `curl` 指令分別戳 `archon-admin` 與 `archon-enduser` 的 Vercel 生產環境網址。
4. **斷言邏輯 (Assertions)**：
   - 擷取回傳的 HTTP Status Code。
   - 如果回傳為 `200` -> 通過 (Pass)。
   - 如果回傳 `>= 400` (如 400, 404, 500, 503) -> 觸發 `exit 1`，讓 Actions 判定為失敗 (Fail)，觸發告警通知。

### Phase 2: (可選/進階) 網頁白畫面防禦 (Playwright Smoke Test)
*(如果發現單純戳 HTTP 200 不夠，遇到 React 渲染崩潰時需要此階段)*
1. 利用現有的 `make audit-qa` 架構，抽出一個極簡版的 Playwright 腳本 (`smoke_test.spec.ts`)。
2. 讓 GitHub Actions 在 Headless 瀏覽器中打開 Vercel 網址。
3. 驗證畫面中是否存在關鍵 DOM 元素（例如：「登入按鈕」或「側邊欄」），若找不到代表 React 崩潰 (白畫面)，立即報錯。

## ✅ 成功定義 (Success Criteria)
- [x] 成功在 `.github/workflows/` 新增監控設定檔。
- [x] 觸發手動測試 (workflow_dispatch) 時，能正確辨識 200 與 400 錯誤。
- [x] 不依賴且不消耗任何額外的雲端機器資源（完全利用 GitHub Actions 免費額度）。

# Phase 4.4 QA List (系統校正與商業價值驗收選單)

此文件記錄了 Phase 4.4 開發過程中的關鍵問題 (Q1-Q6) 以及衍生出的驗收細節。

## 1. 核心問題對接 (Phase 4.4 Q&A)

| ID | 問題描述 | 當前狀態 | 驗證說明 |
| :--- | :--- | :--- | :--- |
| **Q1** | 管理權限不足 (Charlie 無法管理團隊) | ✅ 已解決 | 實作 `TeamManagementPage`，Charlie (Manager) 現可查看團隊與 AI Fleet。 |
| **Q2** | 爬蟲回傳 Mock Data | 🧪 調查中 | **證實**: 程式具備實體抓取能力 (Commit `91459c3`)。但 `_fetch_from_104` 內部會因 `limit` 設定 (預設 10) 連續發送 11 個請求，極易觸發 104 攔截。 |
| **Q3** | 管理面板架構優化 | 📋 已設計 | 已規劃「全角色戰情室 (Specialized Panels)」，參考 Admin Panel 佈局。 |
| **Q4** | 任務指派名單不全 | ✅ 已解決 | `TaskModal.tsx` 已整合 `/api/assignable-users` 與 `/api/agents/assignable`。 |
| **Q5** | Blog 內容更新機制 (UPSERT) | ✅ 已解決 | 遷移腳本已包含 `ON CONFLICT DO UPDATE` 邏輯。 |
| **Q6** | AI 協作 (Jules + AutoGen) | 🔄 待對接 | 基礎架構已規劃，需實作 Jules Adapter 與 AutoGen Sandbox。 |

---

## 2. 使用者回饋與衍生問題 (User Feedback & Issues)

### 【重點 1】爬蟲真實性深度調查 (Q2)
- **調查結果**: 
    - `python/src/server/services/job_board_service.py` 確實有實作 AJAX 模擬，並能在 `test_crawler.py` 獨立執行時成功。
    - **關鍵瓶頸**: 現有邏輯是「一次抓 10 筆」，這意味著會連續發送 11 個 Request（1 個列表 + 10 個詳情）。在 Docker 或頻率稍高時，104 會回傳 403 並導致系統自動降級回 `MOCK_DATA`。
- **對策**: 
    1. 將預設 `limit` 調降（例如 3-5）或引入隨機延遲。
    2. **UI 優化**: 在 `Sales Intel` 頁面顯示「數據來源標記 (Source Badge)」，若因網路被鎖，應給予警告而非靜默降級。
    3. **導航優化**: Alice 的導航應從 `Market Intel` 更名為 `Sales Intel` 以符合語境。

### 【重點 2】多角色專屬「戰情室」規劃 (Q3)
參考 `Admin Panel` 的垂直導航與模組化版型，為每個人量身打造 Panel：

| 角色 | Panel 名稱 | 核心功能 (參考 Admin Panel 版型) | 商業價值 |
| :--- | :--- | :--- | :--- |
| **Admin (You)** | **System Console** | 使用者管理、版本控制、Blog 管理、系統設定、隱私權轉移 | 維運與合規 |
| **Charlie (Manager)**| **Team War Room** | **成員管理 (密碼/權限)**、OKR 儀表板、AI 預算 (Token) 控管、提案審核 (Approvals) | 團隊產能與審核 |
| **Alice (Sales)** | **Sales Nexus** | **Sales Intel (104 爬蟲)**、Leads/Vendors 管理、開發信生成、追蹤提醒 | 業績轉換 |
| **Bob (Marketing)** | **Brand Hub** | **品牌資產 (Logo SVG)**、Blog 內容規劃、市場洞察分析 (Market Specs) | 品牌一致性 |

### 【重點 3】企業執行腳本與人機協作 SOP
- **核心目標**: 證明經過人機協作腳本，兩天工作量可於一小時內完成。
- **標準作業程序 (SOP)**:
    1. **[Admin]**: 執行 `make db-init` 初始化系統 -> 通過 `dev-token` 快速跳轉角色驗證。
    2. **[Alice/MarketBot]**: 登入 `Sales Nexus` -> 啟動 104 爬蟲 -> 自動存入 `Leads` 並由 `MarketBot` 生成開發信草稿。
    3. **[Bob]**: 登入 `Brand Hub` -> 基於 Alice 的 Leads 數據，調整部落格關鍵字並生成文章，提交給經理審核。
    4. **[Charlie/POBot]**: 登入 `War Room` -> 查看 Pending 任務 -> 呼叫 `POBot` 優化 User Story -> 指派給 `DevBot` 執行。
    5. **[DevBot]**: 根據規格生成代碼或 Logo -> 建立 `Proposed Change`。
    6. **[Charlie/Admin]**: 透過 `Approvals` (Admin 版型) 實體預覽變更 -> 一鍵部署。
    7. **[結案驗證]**: Admin 修改全體成員密碼 (Work routine) -> 確認系統自癒。

---
---

## 3. 數據分析 (Commit Data Analysis)

根據 Git Log 分析，Phase 4.4 主要集中在：
1. **結構校正**: 強化資料庫 Schema 與 RBAC 邏輯 (Commit `1e756c3`, `b8f290b`).
2. **爬蟲進化**: 從靜態爬取轉向 104 AJAX 模擬 (Commit `91459c3`).
3. **穩定性**: 建立 E2E 測試保護網.

**待加強區域**: UI/UX 的一致性 (Logo) 與 AI Factory 的實際對接 (Jules/AutoGen).

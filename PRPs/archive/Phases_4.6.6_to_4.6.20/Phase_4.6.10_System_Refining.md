# Phase 4.6.10: 系統優化、專業版升級與架構重構 (System Refining & Pro Upgrades)

## 核心目標 (Core Objectives)
本階段著重於解決系統運作的痛點（Render 效能瓶頸、無效的定時查詢）、梳理雜亂的資料（種子資料清理），並以「不重複造輪子」為原則，拼裝現有零件來提升專業感與開發者體驗。

這不是一份發散的討論清單，而是一份**具備前後相依性的全域執行計畫表**。

---

## 執行計畫表 (Master Execution Plan)

### Step 1: 基礎環境淨化 (Seed Data & Dev Tools) - *優先執行*
**目標**：清除環境中的雜音，讓後續開發與測試專注於真實情境。
*   **1.1 徹底清理髒資料**：
    *   直接刪除 `migration/0.2.1/seed_mock_data.sql` 中的 `Legacy Corp` 等無效 Leads。
    *   直接刪除 `migration/0.2.1/seed_blog_posts.sql` 中的 `SAS` 等非真實案例文章。
    *   確保 `make db-init` 後的環境乾淨且具備必要的基礎設定 (Admin 用戶、系統 Prompts)。
*   **1.2 確立設定權威 (SSOT)**：
    *   將 RAG 與 Crawler 的深層設定徹底收攏至 `Port 3737` (archon-ui-main)。
    *   將 `Port 5173` (enduser-ui-fe) 的 Admin 頁面精簡化，移除冗餘的設定項，轉型為純粹的「系統狀態指標看板」與「文件版本追蹤中心」。

### Step 2: 解決 Render 效能與排程罷工 (Scheduler Architecture) - *核心架構調整*
**現狀問題**：目前的排程器 (`Clockwork`) 綁死在 Render (0.2 CPU) 的 API 伺服器內，只要 API 關閉或休眠，每日的爬蟲與分析就會罷工，且拖垮微弱的伺服器效能。
**解決策略**：
*   **2.1 排程雙軌化 (Dual-Path Scheduling)**：
    *   **主路徑 (Internal)**: 實作基於 `archon_settings` 的物理狀態追蹤，解決重啟失效。
    *   **備援路徑 (External Webhook)**: 物理掛載於 `POST /api/internal/cron/trigger`，受 `ARCHON_CRON_SECRET` 保護，用於應對 API 伺服器長期休眠。

*   **2.2 外部驅動**：
    *   在開發/測試期：寫一個簡單的腳本手動打 API 測試。
    *   在正式環境：捨棄 Render 內部的排程，改用**外部的 Cron 服務** (例如 GitHub Actions Cron, Supabase pg_cron, 或 Render 的 Cron Job 功能) 來定期呼叫這個 Webhook。這樣即使 API 伺服器休眠，外部請求也會將其喚醒並執行任務，且不再長期占用 CPU 資源來防空轉。
*   **2.3 排程任務除錯與修復**：
    *   [已修復] **寫入 `archon_tasks` 失敗 (Log Patrol)**：程式嘗試指派修復任務給系統預設的 `ai-dev-bot`，但因為 `profiles` 表中尚未建立這個使用者的 ID，導致外鍵約束 (Foreign Key constraint) 報錯。
    *   [已修復] **分派任務失敗 (Task Dispatcher)**：在查詢與更新任務狀態時，遇到 `invalid input value for enum task_status: "completed"`（PostgreSQL 中 Enum 型別不匹配）而崩潰。

### Step 3: 消除「無效等待」與重構 Nexus (Manager Dashboard) - *UI/UX 優化*
**現狀問題**：Nexus 標榜「每五分鐘掃描一次」，但這造成了每次載入都在跑無效且耗時的 DB 查詢，而且很多指標根本不是五分鐘就會變動的。
**解決策略**：
*   **3.1 指標意義重構**：
    *   打破「每五分鐘全盤掃描」的假象。將卡片分為「即時動態」 (如 Pending Approvals, 剛發生的 Alerts) 與「每日彙整」 (如 Token Burn-up, 團隊協作指標)。
*   **3.2 載入體感最佳化 (Skeleton Screens & 漸進式重構)**：
    *   在優化資料流的同時，我們針對高達 1600 行的 `ManagerNexus.tsx` 進行**漸進式重構**。
    *   第一步就是為各個區塊（如圖表、審核列表）**獨立封裝元件**，並加入 **骨架屏 (Skeleton Loaders)**。載入時不再卡死，立即呈現 UI 骨架，然後分批回填資料。

### Step 4: 「不造輪子」的專業版編輯器 (Pro Blog Editor) - *零件拼裝*
**現狀問題**：目前的部落格編輯器藏在 Modal 裡，無法給客戶展示。您一直沒看到 Diff 的效果。
**解決策略**：
*   **4.1 獨立編輯路由**：將編輯器從 Modal 抽出，擁有專屬的最大化版面。
*   **4.2 導入現成視圖 (`DiffViewer`)**：
    *   我們已經在專案中擁有 `<DiffViewer />` (`enduser-ui-fe/src/components/DiffViewer.tsx`)。這個元件能完美呈現程式碼或文章修改前後的「紅綠底色」差異對比。
    *   在審核文章 (Approval) 與編輯文章的過程中，直接套用此元件，展示 AI 建議修改了哪些字句。
*   **4.3 補足上傳機制**：整合 Supabase Storage 的圖片上傳機制，讓文章內可以真實插入並預覽圖片。

### Step 5: Approvals 介面細節拋光 (UI Polish)
*   完全**保留現有的 Inbox (收件匣) 佈局結構**，因為這是最有效的管理方式。
*   僅進行字體統一 (Inter)、加大留白、調整重點顏色的微調，對齊整體的「旗艦感」。

### Step 6: 系統除錯與版面進階拋光 (Refinements & Bug Fixes)
包含修復任務狀態 Enum 錯誤、修正 Approvals 版面間隙、實作 MainLayout 左側導覽列的縮放以及加入 Agent 初始設定。

### Step 7: Agent RBAC 驗證與進階 UI 拋光
驗證 5 個 AI Agent 的角色權限，加入 Bob 專用的 Pro Editor 收合按鈕，統一全站 `h1` 為 `text-3xl font-bold`，並放大 `MainLayout` 的 Logo 與 Header 空間。

### Step 8: 使用者反饋與深入細節調整 (User Feedback Refinements)
因應即時的反饋，進行了以下深度架構與機制升級：
*   **8.1 狀態化排程器 (Stateful Scheduler)**：捨棄單純的 Memory Job Store，改為每次任務執行後將時間戳記寫入 `archon_settings`。伺服器啟動時，會根據上次執行時間智慧判斷下發頻率，解決 Render 無限重啟導致的計時器歸零問題。
*   **8.2 擴展爬蟲面向 (104 Job Board)**：將 Alice 的自動搜尋關鍵字從 5 個擴展至 6 個，新增 `"Customer Success"` 與 `"AI"` 面向，並設定啟動後 10 分鐘進行首輪掃描，隨後轉為每 24 小時一次。
*   **8.3 Bob 的每日產業市場日報 (Daily Market Report)**：新增專屬排程，每 24 小時觸發一次 `ai-market-bot`，自動調取 Alice 當日抓取的 Leads 資料，並寫作一篇 600 字的大盤趨勢預測部落格草稿。
    *   **2026-03-21 物理落地 (The Loop)**: 已在 `MarketingService.draft_blog` 實作自動持久化至 `blog_posts` 表，狀態設為 `review`，確保 Charlie 可直接審核。

*   **8.4 UI 終極拋光**：
    *   修復 `ApprovalsPage` 頂部仍有白邊的問題（於 MainLayout 為 `/approvals` 加入全版面樣式）。
    *   修復 `BrandLogo` 生成失敗時，文字「Myrmidon」遭 flex 擠壓跑版的問題。

---

## 物理落地查核結論 (Physical Audit Conclusion) - 2026-03-11
*   **執行狀態**: 🟢 **100% 物理落地**
*   **關鍵證據**:
    *   **狀態化排程器**: 提交 `031f9ad` 實作了基於 `archon_settings` 的 `_schedule_stateful_job` 邏輯，徹底解決 Render 重啟導致的排程失效。
    *   **Nexus 重構**: 提交 `e925c14` 將 1500 行之 `ManagerNexus.tsx` 拆分為 10 個組件並導入 Skeleton Screens。
    *   **DiffViewer 整合**: 提交 `a3397db` 完成 `DiffViewer` 於 `/approvals` 頁面之物理掛載。
    *   **資料淨化**: `migration/0.2.1/` 實體 SQL 已移除 `Legacy Corp` 等髒資料。
*   **狀態化排程器**: 提交 `031f9ad` 實作了 `_schedule_stateful_job` 邏輯，並同步落地 Bob 的每日市場日報自動化 (Line 256)。
*   **架構偏差紀錄**: **物理雙軌制落地**。Webhook 路徑已實作備援 (`/api/internal/cron/trigger`)，但目前優先採用內部狀態化硬化，達成自給自足的排程穩定性。

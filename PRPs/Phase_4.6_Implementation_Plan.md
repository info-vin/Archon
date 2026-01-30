# Phase 4.6 實作計畫 (Implementation Plan)

> **目標 (Goal)**: 
> 1. 為 Alice (Sales) 打造 **Mobile-First** 的外勤體驗 (Swipe to Triage, Voice Log)。
> 2. 為 Bob (Marketing) 升級 **Market Intelligence 2.0** (Trends, Sankey) 與 **Asset Config** (Nana Banana)。
> 3. 建立自動化 **Enrichment Loop** (104爬蟲/資料補全/自動歸檔)。

## User Review Required
> [!IMPORTANT]
> **API Key Governance**: Nana Banana 的 API Key 將由 System Admin 透過 `.env` 管理，App 透過 Backend Proxy 呼叫，前端不暴露 Key。
> **Enrichment Policy**: 建立超過 3 天且資料缺漏的 Leads 將被系統自動歸檔 (Auto-Archived)。
> **RLS Enforcement**: 偵測到 `customers` 等表目前為 Unrestricted。本次 Migration 將強制啟用 RLS，請確保 Application (Service Role) 與 User (Authenticated Role) 的存取邏輯正確。

## Proposed Changes

### 1. Database Schema (`migration/`)
#### [NEW] [020_phase46_schema.sql](file:///Users/vincenta/GoogleKwok022/Archon/migration/020_phase46_schema.sql)
- **Security Hardening (RLS Fixes)**:
    - **`customers`**: Enable RLS.
        - `SELECT`: Auth Users (Alice/Bob/Charlie/Admin).
        - `INSERT/UPDATE`: Sales (Alice), Manager, Admin. (Marketing Read-Only).
    - **`archon_logs` & `gemini_logs`**: Enable RLS.
        - `SELECT`: Admin/System_Admin only.
        - `INSERT`: All Auth Users (for app logging) or Service Role only.
- **`visit_logs`**: 儲存外勤拜訪紀錄 (GPS, Voice Transcript, Summary)。
    - RLS: Users can only see their own logs. Manager can see team logs.
- **`leads` Expansion**:
    - `enrichment_status` (pending, success, failed, review_needed)
    - `enrichment_score` (0-100)
    - `auto_archived_reason` (e.g. "stale_data")
- **`marketing_trends`**: 儲存 Bob 的市場趨勢快照 (避免每次即時運算 heavy query)。
- **`subscriptions`**: 儲存 Blog 訂閱者與 Lead 的關聯。

### 2. Backend API (`python/src/server`)
#### [NEW] [visit_log_api.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/api_routes/visit_log_api.py)
- `POST /api/visits`: 上傳錄音檔與 GPS。
    - **Logic**: 呼叫 Gemini Multimodal API 轉錄音訊 -> 提取摘要 -> 存入 DB。
- `GET /api/visits/user/{user_id}`: Alice 的拜訪歷史。

#### [MODIFY] [marketing_api.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/api_routes/marketing_api.py)
- `GET /api/marketing/trends`: 回傳時間序列與 Sankey 數據 (讀取 `marketing_trends` 表)。
- `POST /api/marketing/nana-banana`: Backend Proxy for Image Generation.
    - **Security**: 讀取 `os.getenv("NANA_BANANA_KEY")`。

#### [NEW] [enrichment_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/enrichment_service.py)
- `enrich_lead(lead_id)`: 嘗試呼叫 `JobBoardService` 或 Google Search 補全資料。
- `prune_stale_leads()`: Cron Job 邏輯，歸檔過期 Leads。

### 3. Frontend (`enduser-ui-fe`)
#### [MODIFY] [Layout.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/components/Layout.tsx)
- **Adaptive Navigation**:
    - Desktop: 保持 Sidebar。
    - Mobile: 自動切換為 **Bottom Navigation Bar** (Dashboard, Leads, Cart, Menu)。

#### [NEW] [LeadsCardStack.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/LeadsCardStack.tsx)
- **Tinder-Style UI**:
    - 使用 `framer-motion` 實作 Swipe Gestures。
    - Right (Like) -> Add to "Sales Cart".
    - Left (Pass) -> Archive.

#### [NEW] [SalesCartPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/SalesCartPage.tsx)
- **Batch Actions**: Export to CRM, Request Content.

#### [MODIFY] [BrandPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/BrandPage.tsx)
- **Market Intelligence 2.0**:
    - 整合 `Recharts` 繪製 Line Chart (Trends) 與 Sankey Diagram (Industry-Need-Solution)。

## Verification Plan

### Automated Tests
- `test_visit_log_api.py`: 測試 Visit Log 寫入與 Gemini Mock 回傳。
- `test_enrichment_service.py`: 測試 Leads 補全邏輯與 Auto-Prune 規則。

### Manual Verification
1.  **Mobile View**: 使用 Chrome DevTools (iPhone 12 view) 驗證 Bottom Nav 與 Card Swipe。
2.  **Voice Log**: 上傳測試音檔，確認 Transcript 正確存入 DB。
3.  **Nana Banana**: Admin 設定假 Key，Bob 頁面呼叫 Proxy，驗證後端正確轉發。

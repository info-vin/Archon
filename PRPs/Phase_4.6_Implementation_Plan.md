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
- [x] **Security Hardening (RLS Fixes)**:
    - **`customers`**: Enable RLS.
    - **`archon_logs` & `gemini_logs`**: Enable RLS.
- [x] **`visit_logs`**: 儲存外勤拜訪紀錄 (GPS, Voice Transcript, Summary)。
- [x] **`leads` Expansion**: `enrichment_status`, `enrichment_score`, `auto_archived_reason`.
- [x] **`marketing_trends`**: 儲存 Bob 的市場趨勢快照。
- [x] **`subscriptions`**: 儲存 Blog 訂閱者與 Lead 的關聯。

### 2. Backend API (`python/src/server`)
#### [NEW] [visit_log_api.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/api_routes/visit_log_api.py)
- [x] `POST /api/visits`: 上傳錄音檔與 GPS。(Implemented Text-only fallback)
- [x] `GET /api/visits/user/{user_id}`: Alice 的拜訪歷史。

#### [MODIFY] [marketing_api.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/api_routes/marketing_api.py)
- [x] `GET /api/marketing/trends`: 回傳時間序列與 Sankey 數據。
- [x] `POST /api/marketing/nana-banana`: Backend Proxy for Image Generation.

#### [NEW] [enrichment_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/enrichment_service.py)
- [x] `enrich_lead(lead_id)`: 嘗試呼叫 `JobBoardService` 或 Google Search 補全資料。
- [x] `prune_stale_leads()`: Cron Job 邏輯，歸檔過期 Leads。

### 3. Frontend (`enduser-ui-fe`)
#### [MODIFY] [Layout.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/components/Layout.tsx)
- [x] **Adaptive Navigation**: Mobile Bottom Navigation Bar.

#### [NEW] [LeadsCardStack.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/LeadsCardStack.tsx)
- [x] **Tinder-Style UI**: Swipe Gestures (Like/Pass).

#### [NEW] [SalesCartPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/SalesCartPage.tsx)
- [x] **Batch Actions**: Export to CRM, Request Content.

#### [MODIFY] [BrandPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/BrandPage.tsx)
- [x] **Market Intelligence 2.0**: Line Chart (Trends) & Sankey Diagram.

### 4. Bob (Marketing) - Visualizations (Frontend Only)
#### [MODIFY] [BrandPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/BrandPage.tsx)
- [x] **TrendLineChart Component**: `recharts` LineChart.
- [x] **Relationship Mapping**: `d3-sankey` or SVG implementation.

### 5. Charlie (Manager) - Tablet Experience
#### [MODIFY] [TeamManagementPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/TeamManagementPage.tsx)
- [x] **AI Collaboration Widget**: Humans vs AI Task Time (Pie Chart).
- [x] **Touch Optimization**: Large touch targets.

#### [MODIFY] [ApprovalsPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/ApprovalsPage.tsx)
- [x] **Card-Based Interface**: Grid layout for tablet.

### 6. UX Polish & Gap Closure
> [!IMPORTANT]
> 補齊 Phase 4.6 UX Strategy 中被延後的 "Nice-to-Have" 但對 Mobile 體驗至關重要的功能。

#### [MODIFY] [SalesCartPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/SalesCartPage.tsx)
- [x] **Batch Actions**:
    - 實作 "Export to CRM" (模擬) 與 "Request Content" (觸發 Magic Draft) 按鈕。
    - 顯示目前 Cart 中的 Leads 清單。

#### [MODIFY] [MarketingPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/MarketingPage.tsx)
- [x] **Clean UI**:
    - 移除 "View Link" 跳轉按鈕，改為 **Click-to-Expand**。
    - Action: "Add to Leads" (觸發 Lead Creation)。

#### [MODIFY] [LeadsCardStack.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/features/marketing/components/LeadsCardStack.tsx)
- [x] **Floating Action Button (FAB)**:
    - Actions: `Map` (Google Maps), `Pitch` (Alert/Modal).

### 7. Mobile & Intelligence Completion (Gap Closure)
> [!IMPORTANT]
> Addressing High-Impact Gaps identified in Phase 4.8 Verification.

#### [NEW] [VoiceService] (Backend & UI)
- [ ] **Voice Logs**:
    - Backend: Integrate Gemini Multimodal API for Audio -> Text.
    - Frontend: Add "Record" button in `VisitLogModal` using MediaRecorder API.

#### [MODIFY] [LeadsCardStack.tsx]
- [ ] **Mobile Pitch experience**:
    - Replace `alert()` with a Fullscreen Drawer/Modal.
    - Features: Large Text, Copy Button, Share Intent.

#### [NEW] [LeadsTimeline.tsx]
- [ ] **Timeline View**:
    - Visual representation of Lead Progression (New -> Contacted -> Meeting -> Deal).

#### [NEW] [ClockInWidget.tsx]
- [ ] **Dashboard Integration**:
    - Large "Clock In/Out" button on Mobile Dashboard.

#### [MODIFY] [BrandPage.tsx]
- [ ] **Smart Image Picker**:
    - Auto-fetch images based on keywords (Automation).
- [ ] **RAG Transparency**:
    - Show Knowledge Base citation metrics (Ref Links %).

## Verification Plan

### Automated Tests
- [x] `test_visit_log_api.py`: 測試 Visit Log 寫入與 Gemini Mock 回傳。
- [x] `test_enrichment_service.py`: 測試 Leads 補全邏輯與 Auto-Prune 規則。

### Manual Verification
1.  [x] **Mobile View**: 使用 Chrome DevTools (iPhone 12 view) 驗證 Bottom Nav 與 Card Swipe。
2.  [x] **Voice Log**: 上傳測試音檔 (Text Fallback)，確認存入 DB。
3.  [x] **Nana Banana**: Admin 設定假 Key，Bob 頁面呼叫 Proxy，驗證後端正確轉發。

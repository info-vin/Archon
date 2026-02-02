# Phase 4.6.2 缺陷與缺口追蹤表 (Bug & Gap Tracking Report)

> **文件目的**: 集中管理 Phase 4.6.2 (Bob Workflow) 與相關 UI 回饋的修復進度。
> **參考標準**: 遵循 Phase 4.6.1 格式。

---

## 📊 摘要儀表板 (Summary Dashboard)

|指標 (Metric)|數量 (Count)|詳細資訊 (Details)|
|:---|:---|:---|
|**總議題數**|8|4 項功能缺陷 (Bug) + 3 項 UI/UX 改善 + 1 項潛在環境問題。|
|**已修復**|0|剛建立報告，待處理。|
|**待處理**|8|全數待處理。重點在於 Nana Banana 與 Magic Draft 的體驗優化。|

---

## 🔍 缺陷與缺口追蹤詳表 (Defect & Gap Tracking Table)

| ID | 類型 (Type) | 功能模組 (Function) | 問題描述 (Description) | 嚴重度 (Severity) | 狀態 (Status) | 相關檔案 (Trace) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-023** | 🐛 Bug | **Environment** | Google RAG 設定狀態異常 (紅叉)，但 DB 有 Key。需確認 API 快取或載入邏輯。 | High | 🔴 待處理 | `providers_api.py` |
| **BUG-024** | 🐛 Bug | **Nana Banana** | 圖片生成失敗，缺明確錯誤訊息。腳本落地與儲存邏輯不明。 | High | 🔴 待處理 | `marketing_api.py` |
| **BUG-025** | 🐛 Bug | **Magic Draft** | 切換分頁導致 Draft 內容遺失。需實作 State Persistence。 | High | 🔴 待處理 | `ContentWorkbench.tsx` |
| **BUG-026** | 🐛 Bug | **Workbench** | Save 按鈕點擊後無反饋 (Toast/Redirect)，使用者不知資料去向。 | Medium | 🔴 待處理 | `ContentWorkbench.tsx` |
| **UX-008** | 🔧 Gap | **Workbench/UI** | 雙重捲軸 (Double Scrollbar) 體驗不佳。需鎖定外層，僅讓內容區滾動。 | Medium | 🔴 待處理 | `BrandPage.tsx` |
| **UX-009** | 🔧 Gap | **Market Trend** | 缺少數據資料，且版面需移至 Post Editor 上方 (參考 Figma)。 | Low | 🔴 待處理 | `WorkbenchArea.tsx` |
| **UX-010** | 🔧 Gap | **Icon Gen** | Icon Generator 位置需調整至 Post 流程下方。 | Low | 🔴 待處理 | `WorkbenchArea.tsx` |

---

## 📝 詳細問題說明 (Detailed Issues)

### 1. 環境與設定 (Environment & Config)

#### [BUG-023] Google RAG 設定狀態異常 (Red Cross)
- **症狀**: Admin UI (Port 3737) 的 RAG 設定頁面，Google Provider 顯示紅叉 (Not Configured)。
- **分析**:
    - `make db-init` 已成功將 `GOOGLE_API_KEY` 寫入 `archon_settings` 資料庫表。
    - `docker exec` 驗證資料庫中確實存在 Key。
    - 但 `/api/providers/google/status` 回傳 `no_key`，顯示後端 `providers_api` 在讀取 `CredentialService` 時發生異常（可能是快取或啟動時序問題）。
- **影響**: 無法確認 RAG 是否真正使用 Google 模型，給使用者帶來不安全感。

### 2. 功能邏輯 (Functional Logic)

#### [BUG-024] Nana Banana 圖片生成失敗
- **症狀**: 點擊 "Generate Image" (或是 Nana Banana 按鈕) 失敗。
- **疑問**: 使用者不清楚腳本是如何落地的？(是直接存進 DB？還是存到 Storage？檔名邏輯為何？)
- **預期**: 應有明確的錯誤訊息，且生成的圖片應有可追蹤的 URL。

#### [BUG-025] Magic Draft 資料遺失 (State Persistence)
- **症狀**: 點擊 "Magic Draft" 開始生成後，若切換到其他 Tab 或頁面，再切換回來會顯示 `Loading`，且原本生成的內容全部消失。
- **痛點**: 使用者被迫必須「盯著螢幕」直到生成完成，無法多工處理。
- **建議**: Draft State 應該 persist 在 LocalStorage 或 Redux 中，或者後端生成任務應該是背景執行的，切換回來後能 polling 到結果。

#### [BUG-026] Save 按鈕無反饋
- **症狀**: 點擊 "Save" 按鈕後，介面沒有任何 Toast 訊息或視覺反饋。
- **疑問**: 「存到哪裡去了？」
- **預期**:
    - 成功時顯示 "Draft Saved" 綠色 Toast。
    - 失敗時顯示錯誤原因。
    - 資料應存入 `blog_posts` 表，狀態為 `DRAFT`。

### 3. UI/UX 改進 (Design Polish)

#### [UX-008] Workbench 捲軸體驗不佳 (Double Scrollbar)
- **症狀**: 「上下還要拖曳兩次？一次瀏覽器，一次 Workbench？」
- **分析**: Workbench 內部容器 (`SplitPane`) 可能設定了 `overflow-y-scroll`，而外層 `BrandPage` 或 `Layout` 也有捲軸，導致雙重捲軸。
- **建議**: Workbench 應佔滿剩餘高度 (`flex-1 h-full`)，並鎖定外層捲軸，只讓內部內容區滾動。

#### [UX-009] Market Trend 區塊改版
- **現狀**: 目前無資料。
- **需求**:
    - 仍需要數據資料展示。
    - 版面移至 **Post Editor 上方**。
    - 參考 Figma 版型。
    - 考慮「日夜切換」樣式。

#### [UX-010] Icon Generator 位置調整
- **需求**: 將 Insight 的 icon 產生器移至 **Post 流程的下方**。

---

## 🛠 修復紀錄 (Fix Log)

*   **2026-02-02**:
    *   **初始化**: 建立追蹤報告，彙整 User 回饋的 7 項議題。
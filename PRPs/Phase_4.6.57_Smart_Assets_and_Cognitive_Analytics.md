# Phase 4.6.57: 智慧資產 (Smart Assets) 與 認知分析 (Cognitive Analytics)

> **文件狀態**: 📝 規劃中 (2026-05-08)
> **目標**: 深化 Bob (Marketing) 的內容生產力與 David (Admin) 的系統治理能力。落實「先設計狀態，再寫 UI，且必附 MBT 測試」的開發鐵律。

## 1. 執行摘要

本階段聚焦於將 Phase 4.6 中的「Mock 智慧化」轉變為「實體智慧化」，並建立系統自我觀察的認知閉環：
1. **Bob (Marketing) - 實體智慧圖庫**: 實作 `SmartImagePicker`，串接真實搜尋 API (如 Unsplash) 並由 XState 管理搜尋狀態。
2. **Bob (Marketing) - RAG 引用透明化**: 在內容生成中標註知識庫來源，並提供跳轉驗證 UI。
3. **David (Admin) - AI 修改率追蹤**: 實作 AI 生成內容的「前後對照 (Diff)」紀錄，並建立認知分析看板。

---

## 2. Bob (Marketing): 智慧資產硬化 (Smart Assets Hardening)

### 2.1. 智慧圖庫 (Smart Image Picker)
- **狀態設計 (`imagePickerMachine.ts`)**: 
    - 狀態: `idle`, `searching`, `success`, `error`, `selecting`.
    - 行動: `search(keyword)`, `select(image_url)`, `retry()`.
- **UI 實作 (`SmartImagePicker.tsx`)**: 
    - 採用 Radix UI Dialog 承載。
    - 支援關鍵字搜尋與圖片預覽。
- **MBT 驗證**: `ImagePicker.mbt.spec.ts` 驗證在 API 延遲與空結果下的 UI 行為。

### 2.2. RAG 引用透明化 (RAG Citations)
- **UI 實作**: 在 `BlogWorkbench` 中實作 `CitationBadge`。
- **資料流**: 後端 `MarketingService` 在生成內容時，需在 `details` 中包含 `source_references` (文件 ID 與 區塊)。

---

## 3. David (Admin): 認知分析與自癒 (Cognitive Analytics)

### 3.1. AI 修改紀錄 (Correction Tracking)
- **後端擴充**: 
    - 在 `MarketingService.updateBlogPost` (或專屬 API) 中，比對 `original_content` (AI 生成) 與 `final_content` (人類修改)。
    - 使用 `archon_logs` (Type: `AI_CORRECTION`) 儲存差異 (Diff) 數據。
- **分析看板 (`AdminCorrectionAnalytics.tsx`)**:
    - **狀態設計 (`analyticsMachine.ts`)**: 管理數據加載與過濾狀態。
    - **視覺化**: 顯示各 Prompt 版本的「人類修正率」趨勢圖。

---

## 4. 核心開發鐵律執行方案 (Iron Law Enforcement)

### 步驟 A: 狀態優先 (State First)
- 在撰寫任何 React 元件前，必須先建立並展示 `machine.ts`。使用 XState `setup` 模式，明確定義 `context`, `events`, 與 `actors`。

### 步驟 B: 物理對齊 (Physical Parity)
- 圖片搜尋 API 必須具備真正的後端 Proxy 或 100% 擬真的 Stateful Mock。
- 修改紀錄必須真正寫入資料庫，並通過 `make persona-audit` 驗證權限隔離。

### 步驟 C: MBT 覆蓋 (MBT Always)
- 每個新功能必須附帶 `*.mbt.spec.ts`。
- 測試必須包含「負面路徑」：API 500、網路超時、無搜尋結果。

---

## 5. 實作路徑 (Implementation Path)

- [x] **Step 1**: 建立 `features/marketing/machines/imagePickerMachine.ts`。
- [x] **Step 2**: 實作 `SmartImagePicker.tsx` 並集成至部落格工作台。
- [x] **Step 3**: 撰寫 `ImagePicker.mbt.spec.ts`。
- [x] **Step 4**: 後端實作 `AI_CORRECTION` 紀錄邏輯。
- [ ] **Step 5**: 建立 `features/admin/components/CorrectionAnalytics.tsx` 並撰寫 MBT。

---

## 6. 驗證標準 (Definition of Done)
1. `npx playwright test` 全綠，包含異常狀態模擬。
2. David 可以在 Admin UI 看到 Bob 剛剛修改文章所產生的修改百分比。
3. Bob 可以點擊文章中的引用標籤直接查看 RAG 知識庫來源。

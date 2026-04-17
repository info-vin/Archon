# Phase 4.6.42: Deep RAG Optimization & Marketing Intelligence 2.0

> **目標 (Goal)**: 提升 RAG 檢索精確度（導入 Contextual Retrieval）並實作 Bob 的高價值名單分析面板。
> **核心對帳**: 目前 RAG 知識庫僅 46 Chunks 且缺乏脈絡；86 筆 Leads 缺乏視覺化轉化指標。

---

## 1. 物理落地計畫 (Implementation Plan)

### A. Deep RAG Optimization (Contextual Retrieval)
*   **現狀**: 傳統 RAG 切片導致脈絡斷裂（如「該公司」不知道是哪家公司）。
*   **任務**:
    1.  **Service 優化**: 已更新 `contextual_embedding_service.py`，採用 Gemini 2.5 Flash 進行「情境植入 (Situating)」。
    2.  **數據升級**: 已完成 17/46 個既有切片的物理升級（受限於 Gemini Free Tier 配額，其餘將批次處理）。
    3.  **Hybrid Search**: 物理確認 `rag_service.py` 已啟用 Vector + Keyword 混合檢索。

### B. Marketing Intelligence 2.0 (Bob's Panel)
*   **現狀**: 具備 86 筆 Leads 數據，但缺乏 ROI 與轉化率視覺化。
*   **任務**:
    1.  **指標實作**: 在 `metrics.py` 實作 `Lead Conversion Velocity` (轉化速度) 與 `Knowledge ROI`。
    2.  **ASCII 視覺化**: 在後端日誌或 Admin UI 輸出實體轉化漏斗。
    3.  **前端掛鉤**: 在 `Brand Hub` 頁面顯示「產業需求分佈圖」與「轉化潛力評分」。

---

## 2. 實作路徑 (Action Items)

- [x] **Task 1**: 升級 `contextual_embedding_service.py` 邏輯 (Gemini 2.5 Flash + 20k context)。
- [ ] **Task 2**: 實作 `LeadScoringService` 根據 job_title 自動評估 Leads 價值。
- [ ] **Task 3**: 批次完成剩餘 29 個 RAG 切片的優化。
- [ ] **Task 4**: 在 5173/bob 頁面實作 `ConversionFunnel` 組件。

---

## 3. 驗證標準 (Verification)
1.  **RAG**: 檢索「軟體整合策略」時，回傳的 Chunk 包含「這份文件關於 Opcenter APS...」的植入脈絡。
2.  **Bob**: 儀表板正確顯示 69 筆 New Leads 的產業佔比。

---

## 4. 結案狀態
- **狀態**: ⏳ **執行中** (2026-04-17)
- **證據**: 17/46 Chunks 已物理優化。

# Phase 4.6.26 實作計畫 - Industrial RAG & 5173 Governance Alignment

> **目標 (Goal)**: 
> 1. **工業級 RAG**：實作語境指紋注入 (Contextual Header Injection)，提升檢索精確度。
> 2. **5173 數據對齊**：確保 156 資源的檢索權重與來源物理顯示於 5173 Dashboard。
> 3. **透明化硬化**：確保 Reranking 分數與原始片段路徑在 5173 可視化。

## 1. 物理修復清單 (Action Items)

- [ ] **Task A: 語境指紋注入 (Contextual Injection)**
    - 修改 `document_processing.py`：在切片時物理注入 `[Source: {filename} | Section: {header}]`。
- [ ] **Task B: 5173 檢索渲染硬化**
    - 物理檢查 `KnowledgeROI.tsx`：確保其解析邏輯能正確處理 NFC 淨化後的數據。
- [ ] **Task C: RAG 幻覺門禁預研**
    - 研究如何在後端加入相似度與忠實度 (Faithfulness) 的物理指標。

## 2. 物理驗證計畫 (Verification)

- [ ] **指紋測試**：重新上傳 156 資源，搜尋結果應自帶來源標註。
- [ ] **5173 對帳**：在 5173 UI 物理看到檢索片段的章節來源。

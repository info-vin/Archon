# Phase 4.6.25 實作計畫 - Knowledge Hardening & Admin UI Audit

> **目標 (Goal)**: 
> 1. **編碼硬化**：解決 RAG 檢索中的亂碼問題，確保從提取到回傳的物理編碼一致性。
> 2. **性能優化**：預加載 Reranking 模型，消除 15 秒的冷啟動延遲。
> 3. **UI 完整性稽核**：物理檢查 3737 Admin UI 的功能遺漏，確保與 4.6.24 重構後的 API 100% 對齊。

## 1. 物理修復清單 (Action Items)

- [x] **Task A: 編碼一致性硬化** (🟢 已完成)
    - 修改 `document_processing.py`：確保 `extract_text_from_document` 回傳標準 UTF-8 NFC。
- [x] **Task B: Reranking 預加載** (🟢 已完成)
    - 在 `main.py` 的啟動序中物理啟動模型預加載。
    - 實作了 `RerankingStrategy` 單例模式，消滅重複加載開銷。

- [x] **Task C: 跨端功能分工對帳** (🟢 已完成)
    - 物理對帳結論：3737 定位於「系統底層配置」(RAG 參數, API Keys, Migrations)；5173 定位於「業務運行治理」(ROI, XP Ranking, User Management)。
    - 驗證通過：3737 的 `SettingsPage` 已物理包含 RAG 調校開關，5173 已物理包含 ROI 儀表板。


## 2. 物理驗證計畫 (Verification)

- [ ] **RAG 亂碼測試**：再次執行 156 搜尋，驗證 `content` 欄位不再出現轉義亂碼。
- [ ] **冷啟動測試**：重啟 Docker 後，第一次搜尋應在 2 秒內回傳（目前為 15 秒）。
- [ ] **UI 功能對帳表**：產出 3737 的功能完整性報告。

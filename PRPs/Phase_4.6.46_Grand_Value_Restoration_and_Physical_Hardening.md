# Phase 4.6.46: 核心價值回歸與物理硬化 (Grand Value Restoration & Physical Hardening)

## 📌 執行背景
在 Phase 4.6.45 完成全系統「對帳清掃」後，我們發現了嚴重的「考古式退化」：系統弄丟了 2 月份已經實現的 5 大高級生產力功能。
本階段的目標是：**物理找回失落的邏輯，並使用「Git 守門員」與「物理斷言」鎖死這些功能，防止再次退化。**

## 🗺️ 失落功能恢復地圖 (Restoration Map)

### 1. 恢復 Files API 轉錄鏈條 (Alice / GAP-009)
*   **來源**: `40c92ce` (2026-02-06)
*   **物理現狀**: 當前代碼退化回 Base64，大檔案必崩。
*   **行動**: 恢復 `upload_file_to_google` 邏輯，並對齊 `SYSTEM_MODELS["DEFAULT_TEXT"]`。
*   **驗證**: 上傳大於 10MB 的音訊檔案，轉錄成功且無 Time-out。

### 2. 恢復 創意韌性 EXP-03 (Bob / Milestone)
*   **來源**: `b6af562` (2026-02-16)
*   **物理現狀**: `MarketingService` 中的情感/語氣修正邏輯完全失蹤。
*   **行動**: 重新注入「語氣約束 (Tone Constraints)」檢索與 LLM 循環修正邏輯。
*   **驗證**: 生成內容後，主動檢查是否符合 `archon_settings` 中的品牌規範。

### 3. 恢復 孿生反饋閉環 (Digital Twin)
*   **來源**: `6817712` (2026-02-25)
*   **物理現狀**: Scout 僅存日誌，無反饋邏輯。
*   **行動**: 將 `twin_scout.py` 的分析結果物理掛鉤至 `AgentRegistry` 的動態權重。
*   **驗證**: 執行 `make twin-scout` 後，系統應能自動調優 Agent 的工具權限。

### 4. 恢復 哨兵瓶頸檢測 (Charlie / SEN-003)
*   **來源**: `970ed30` (2026-02-03)
*   **物理現狀**: 僅有表名修復，缺乏「內容瓶頸」的實體檢測代碼。
*   **行動**: 補齊 Leads 逾期、內容排隊與成本預警的報警邏輯。
*   **驗證**: 手動注入一筆逾期 Lead，Scheduler 應產出 `INFO` 報警。

### 5. RAG 實體掃描門禁 (Librarian)
*   **物理現狀**: 目前僅有靜默 fallback。
*   **行動**: 重新恢復 `db_probe.py` 的 768 維度硬斷言。
*   **驗證**: 如果向量維度不對齊，`make probe` 必須報錯並退出。

## 🛡️ 守門員公證 (Gatekeeper Notary)
- [x] 已建立 `.git/hooks/pre-commit` 阻斷舊模型與舊表名。
- [ ] 執行 `make lint` 確保恢復後的邏輯符合 4.6.45 的品質標準。

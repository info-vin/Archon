# Archon Testing & Audit Matrix

## 測試演進脈絡與痛點反思 (Historical Context & Pain Points)

正如我們在開發歷程中所體會到的，這套系統之所以演進到如此複雜的「三層防禦」（單元測試 -> E2E -> 孿生錄影），是因為在早期的開發過程中，我們面臨了大量的**「開發結果與驗收標準不符」**的痛點：

1. **盲目開發與回歸 (Blind Development & Regression)**：開發初期常發生「修 A 壞 B」，或是「昨天改今天壞」的狀況。這迫使我們導入 TypeScript Playwright 作為第一道 E2E 防線，強制在 CI/CD 中進行自動化功能驗證。
2. **幽靈開發與視覺不符 (Ghost Development & Parity Mismatch)**：後端 API 寫好了，自動化測試也過了，但 UI 卻沒渲染；或是 UI 寫了假畫面，背後卻沒接 API。為了解決這種「程式碼通過但人眼看起來不對」的痛點，才誕生了 `make twin-scout` (容器化物理對帳)。
3. **驗證與比對的終極手段**：最終，對於複雜的商業邏輯與多 Agent 協作，單純的 DOM 檢查已經不夠。我們需要「錄影驗證結果比對」，將截圖與影片交給 Gemini AI 裁判，用最接近真實用戶的「肉眼」去確認開發結果是否真正符合驗收標準。這正是 `make twin-record` 數位孿生腳本的核心價值。

---

## 數位孿生場景複雜度與覆蓋矩陣 (Twin Scout Scenario Matrix)

基於 Phase 5.4.0 (資料驅動配置) 的精神，我們將目前所有的 YAML 數位孿生腳本依重要程度與複雜度進行量化統計，作為未來的維護與擴充基準：

| 優先級 | 腳本名稱 (Scenario YAML) | 核心目的 (Purpose) | 涵蓋層級 (Scope) | 複雜度 | AI 視覺裁判 | 與 E2E 重疊度說明 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P0** | `marketing_chat` | 驗證星型群聊實體運作 | UI -> DB -> LLM -> AI 協作 | 🔴 極高 | 是 (辨識對話泡泡) | **低**。E2E 無法等待並驗證真實 LLM 群聊結果，此腳本填補了實彈演習的空白。 |
| **P1** | `fanout_executive_summary` | 驗證 Clockwork 背景排程 | Cron -> DB -> UI 聚合 | 🟠 高 | 否 (靜態 DOM 檢查) | **低**。E2E 無法物理觸發背景 Cron Job (Map-Reduce)，此腳本透過 Pre-hook 實現跨界整合。 |
| **P2** | `check_workbench_video` | 驗證 RAG 影音素材渲染 | DB (Regex) -> UI (Media) | 🟡 中 | 是 (辨識播放器 UI) | **中**。E2E 僅能測 `<video>` 標籤，此腳本以 AI 確保播放器控制列與畫面真實渲染成功。 |

*(本矩陣應隨新場景的加入持續更新)*
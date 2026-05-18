# Phase 5.1.4: Librarian - RAG 硬化與獵人模式管線

## Goal Description
本階段聚焦於 **Librarian (知識管理員)** 的核心能力升級。首先解決了 RAG 檢索中「引用不透明」的技術債，確保 AI 的每一句回答都有物理證據可循。接著將實作 **「獵人模式 (Hunter Mode)」** 自動補全管線，讓 Librarian 具備主動獲取外部情報並注入 RAG 的能力。

## 實作進度 (Status)

### 1. RAG 引用透明度 (Citation Transparency) - 🟢 物理落地
*   **[DONE] 實體收集器**: 在 `RagDependencies` 中引入 `collected_citations` 物理緩衝。
*   **[DONE] 工具硬化**: `search_documents_tool` 現在會主動捕獲 Metadata 而非僅回傳字串。
*   **[DONE] UI 閉環**: 前端 `TaskAgentGroupChat` 實作了標籤式引用展示，支援 Hover 預覽。

### 2. 「獵人模式」自動補全管線 (Hunter Mode Pipeline) - 🟢 物理落地 (Ref: Phase 5.1.5)
*   **[DONE] Librarian 擴展**: 為 Librarian 注入 `run_web_crawler` 工具，對接現有的 `CrawlingService`。
*   **[DONE] 臨時知識注入**: 實作 `Librarian` 將爬取內容即時向量化並關聯至當前 `Task` 的邏輯。
*   **[DONE] 多智能體路由**: 在 `Supervisor` 邏輯中定義「線索補全」的特定跳轉路徑。

## User Review Required

> [!IMPORTANT]
> **引用展示策略**: 目前引用會顯示在 Librarian 的每一條對話下方。如果您認為這會導致 UI 過於擁擠，我們可以改為「摺疊式」顯示。
> **爬蟲成本**: 獵人模式會頻繁調用外部爬蟲與 Embedding API，建議在 `archon_settings` 中設定單日調用上限。

## 驗收標準 (Acceptance Criteria)
1. **引用準確性**: UI 顯示的引用序號 `[1]` 必須與 LLM 文本中的序號 100% 物理對齊。
2. **管線連通性**: 當 Alice 觸發線索補全時，Librarian 必須能在背景完成資料抓取，且不阻塞 UI。

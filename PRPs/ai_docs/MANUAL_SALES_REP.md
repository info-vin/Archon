# Case 5 腳本：銷售情資與 RAG 協作 (Sales Intelligence & RAG Workflow)

**文件定位**: 本文件為 `seed_blog_posts.sql` 中 "Case 5" 文章的原始腳本。
**展示目的**: 演示 Archon 如何透過「行銷建置、業務使用」的協作模式，將冷資料轉化為熱訂單。

---

## 角色分工 (Role Separation)

| 階段 | 角色 | 權限要求 | 動作 |
| :--- | :--- | :--- | :--- |
| **Phase 1: 準備** | **Bob (Marketing)** | `can_manage_content` | 上傳 `156_resource` 文件，建立知識庫。 |
| **Phase 2: 執行** | **Alice (Sales)** | `member` (Sales Dept) | 搜尋職缺，生成針對性 Pitch。 |

---

## 劇本流程 (Scenario Script)

### Phase 1: 知識庫武裝 (由 Bob 執行)
> **旁白**: 行銷經理 Bob 收到了一批關於「南非鋰電池市場」與「Fujitec 整合案」的高價值舊文件。他決定將其導入系統，武裝業務團隊。

1.  **登入**: Bob 使用 `bob@archon.com` 登入 Admin/End-User UI。
2.  **上傳**: 進入 **Knowledge Base**，上傳 `160_south_africa_lithium_battery_market_bp.docx`。
3.  **確認**: 系統顯示 "Processing Complete"，文件已向量化。

---

## Phase 2: 獵物搜尋 (由 Alice 執行)
> **旁白**: 業務代表 Alice 正在尋找需要數據整合服務的潛在客戶。

1.  **登入**: Alice 使用 `alice@archon.com` 登入。
2.  **搜尋**: 進入 **Sales Intelligence** (`/marketing`) 頁面，搜尋 `Data Analyst`。
3.  **發現**: 列表出現 "Retail Corp"。
4.  **洞察**: Alice 點擊 **"View Full JD"**，看到對方強調 "Experience with Lithium Market or Energy Sector is a plus" (此為假設的 JD 內容)。

---

## Phase 3: 致命一擊 (RAG 協作)
> **旁白**: 系統發現 Retail Corp 的需求與 Bob 剛剛上傳的知識庫高度相關。

1.  **生成**: Alice 點擊 **"Generate Pitch"**。
2.  **RAG 運作**:
    *   **Input**: Retail Corp JD ("Lithium Market").
    *   **Retrieval**: 系統從知識庫召回 `160_south_africa...docx` 中的關鍵段落。
    *   **Output**: 生成 Email 草稿：「我們注意到貴司正在招募能源領域的數據專家。Archon 團隊剛發布了一份關於南非鋰電池市場的深度報告...」。
3.  **發送**: Alice 複製內容，寄出郵件。

---

## 技術實作筆記 (For Developers)

*   **E2E 測試重點**: 必須驗證 Phase 2 中 Alice 點擊 "Generate Pitch" 時，前端能正確顯示包含 RAG 檢索結果的文字。
*   **權限邊界**: 確保 Alice **無法**看到或執行 Phase 1 的上傳按鈕。
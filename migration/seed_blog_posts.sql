-- migration/seed_blog_posts.sql
-- 向 blog_posts 資料表中插入初始文章資料

-- 確保 blog_posts 資料表存在，如果不存在則建立它
-- 注意：這只是一個範例，真實的 schema 管理應在主 schema 檔案中完成
CREATE TABLE IF NOT EXISTS blog_posts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    excerpt TEXT,
    author_name TEXT,
    publish_date TIMESTAMPTZ,
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ
);

-- 清空現有資料以避免重複插入
TRUNCATE TABLE blog_posts RESTART IDENTITY;

INSERT INTO blog_posts (id, title, excerpt, author_name, publish_date, image_url) VALUES
('post-1', '案例一：AI 助您輕鬆完成行銷素材', '**角色**: 一位行銷專員 (User)。

**目標**: 產出一份新產品的行銷 DM。

**流程拆解**:

1.  **任務啟動 (前端)**
    *   行銷專員登入系統，點擊「新增任務」。
    *   他上傳了 `product_spec.pdf` 和 `copy_draft.txt` 兩個檔案。
    *   他點擊「指派給」下拉選單，選擇了「設計師 AI Agent」。

2.  **後端處理與 Agent 觸發**
    *   後端 API 收到請求，進行權限驗證。
    *   在資料庫建立任務，狀態為 `處理中`。
    *   後端非同步地觸發「設計師 AI Agent」。

3.  **AI Agent 執行**
    *   AI Agent 被喚醒，下載並分析任務文件。
    *   基於內容，它生成了一張圖片檔案 `dm_draft_v1.png`。

4.  **產出交付與任務更新**
    *   Agent 呼叫工具，將 `dm_draft_v1.png` 上傳到 Supabase Storage。
    *   後端更新資料庫任務：狀態改為 `待審核`，並附加檔案 URL。

5.  **使用者審核 (前端)**
    *   行銷專員的介面收到即時更新，看到狀態變更和新的附件連結，點擊審核。', 'Archon 團隊', '2025-08-29T10:00:00Z', 'https://picsum.photos/seed/usecase-1/600/400'),
('post-2', '案例二：從技術支援到知識庫建立的自動化流程', '**角色**: 初階客服、資深後端工程師、知識庫 AI Agent。

**目標**: 解決一個複雜的技術問題，並將解決方案歸檔至內部知識庫。

**流程拆解**:

1.  **問題升級 (客服 -> 工程師)**
    *   初階客服遇到無法解決的 Bug，建立任務並附上日誌，指派給資深後端工程師「陳大哥」。

2.  **人工處理 (工程師)**
    *   陳大哥調查並解決問題，在任務評論區詳細記錄了排查過程和解決方案。

3.  **知識庫歸檔 (工程師 -> AI Agent)**
    *   陳大哥認為此方案有價值，將任務重新指派給「知識庫 AI Agent」，並指示它整理成 Q&A 文件。

4.  **AI Agent 整理與歸檔**
    *   AI Agent 讀取任務歷史，提煉核心內容，生成一份標準化的 Markdown 文件。
    *   它呼叫工具將文件上傳至 Supabase Storage 中名為「internal_knowledge_base」的特定位置。

5.  **任務完成與知識沉澱**
    *   任務狀態變為 `已歸檔`，並附上知識庫文章連結，供團隊未來搜尋參考。', 'Archon 團隊', '2025-08-28T14:30:00Z', 'https://picsum.photos/seed/usecase-2/600/400'),
('post-3', '案例三：業務開發與客戶拜訪的智能規劃', '**角色**: 業務人員「小王」。

**目標**: 蒐集潛在大客戶「ABC 科技」的完整情報，並規劃一次成功的初次拜訪。

**流程拆解**:

1.  **情資蒐集 (智能查詢)**
    *   小王在系統中使用自然語言查詢關於「ABC 科技」的所有資訊。
    *   RAG Agent 在後端搜尋所有關聯資料庫與文件，並生成一份摘要總結，連同原始資料連結一併呈現。

2.  **行動規劃 (任務建立與指派)**
    *   小王根據情資建立父任務「規劃拜訪 ABC 科技」，並設定截止日期。
    *   他建立多個子任務：
        *   指派「行銷 AI Agent」製作客製化簡報。
        *   指派「自己」去和客戶預約時間。
        *   指派「資深工程師」作為技術顧問，準備一同出席。

3.  **協同工作與進度追蹤**
    *   所有相關人員與 AI 都在同一個任務下更新各自的進度與產出（例如，AI 附加簡報草稿、工程師回覆時間）。

4.  **行程確定與完成**
    *   小王在所有準備工作就緒後，敲定會議時間，並在父任務中記錄，完成整個規劃的閉環。', 'Archon 團隊', '2025-08-27T09:00:00Z', 'https://picsum.photos/seed/usecase-3/600/400');

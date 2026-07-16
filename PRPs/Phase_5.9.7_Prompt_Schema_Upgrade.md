# Phase 5.9.7: 提示詞架構擴充與美術語料庫整併 (Prompt Schema Upgrade & Art Prompts Consolidation)

## 🎯 目標 (Goal)
指揮官洞察到原有的 `Art_Asset_Prompts.md` 作為純文字檔，脫離了 `5173` Web UI 的集中管理，產生了 SSOT (單一事實來源) 的管理斷層。
為了解決這個問題，並**精準對齊原有的 Markdown 樹狀架構**，我們必須擴充現有 `archon_prompts` 資料表的 Schema，引入 `category` 與 `metadata (JSONB)` 欄位，將線下文件完美數位化，實現真正的 100% 提示詞統治。

## 🛡️ 行動前風險評估 (改 A 壞 B 防禦)
針對「改 A 壞 B」的疑慮，原先的架構是仰賴「API 無嚴格校驗 (直接回傳 dict)」來避免報錯。但為了**響應對更高代碼品質 (Pydantic 架構對齊) 的要求**，本次升級將正式導入嚴格的 Pydantic 模型驗證：
1. **Pydantic 模型升級**：新增 `schemas/prompts.py` 定義強型別的 `PromptResponse` 與 `PromptUpdateRequest`。
2. **防禦性 JSONB 解析**：在 Pydantic 模型中設定 `extra = "allow"`，並確保 `category` 與 `metadata` 具備預設值 (`SYSTEM_AGENT` 與 `{}`)。即使舊資料缺少欄位，Pydantic 也會自動補齊，**確保 100% 向前相容，絕不觸發 `ValidationError` 崩潰**。
3. **前端寬容性**：5173 Web UI 的 React 元件會自動忽略它不認識的新欄位。

## 🏛️ 架構對齊設計 (ASCII Architecture Design)

```text
=================================================================================================
                 [ DATABASE SCHEMA UPGRADE: archon_prompts ]
=================================================================================================
 
 舊有欄位 (Legacy)                       新增欄位 (New for Phase 5.9.7)
 +-------------------+                  +-----------------------------------+
 | id (UUID)         |                  | category (TEXT)                   |
 | prompt_name (TEXT)|                  |  ├─ SYSTEM_AGENT (預設值)         |
 | prompt (TEXT)     |                  |  ├─ RAG_WORKFLOW                  |
 | description (TEXT)|                  |  └─ ART_ASSET                     |
 | updated_at (TS)   |                  |                                   |
 | is_system_protect |                  | metadata (JSONB)                  |
 +-------------------+                  |  ├─ group (字串)                  |
                                        |  ├─ subgroup (字串)               |
                                        |  ├─ target_file (字串)            |
                                        |  └─ theme (字串)                  |
                                        |                                   |
                                        | ※ UX 考量：為保留「一鍵複製貼上」   |
                                        |    體驗，負向提示詞與參數將直接整合  |
                                        |    進 prompt 欄位中。             |
                                        +-----------------------------------+
```

### 💡 實體映射範例 (Data Mapping Example)

【來源 Markdown 區塊】
### 1.1 戰鬥場景背景 (GameBoard Background)
(隸屬於大類：1. 環境背景)
* 目標檔案：recontextualization/assets/images/bg_vector_grid.png
* Prompt & Settings: POV flying into the matrix... --ar 16:9
* Negative Prompt: text, watermark, characters...
```
⬇️ (無損轉換完整範例)
```json
{
  "prompt_name": "ART_ENV_BATTLE_BG",
  "category": "ART_ASSET",
  "description": "戰鬥場景背景 (GameBoard Background)",
  "prompt": "POV flying into the matrix, an infinite 3D wireframe cyberspace grid tunnel, extreme deep perspective... \n--no text, watermark, characters, people, UI elements, bright light\n--ar 16:9\n(⚠️ 畫師/產圖工具注意：匯出解析度限制 1920x1080)",
  "metadata": {
    "group": "1. 環境背景",
    "subgroup": "1.1 戰鬥場景背景",
    "target_file": "recontextualization/assets/images/bg_vector_grid.png",
    "theme": "深邃的量子資料庫內部..."
  },
  "is_system_protected": true
}
```

## 📋 執行清單 (Proposed Changes)

### 1. 🗄️ Database & Migration (SQL)
- **[NEW]** `migration/0.2.2/30_alter_archon_prompts_schema.sql`
  - 使用 `ALTER TABLE archon_prompts ADD COLUMN category text DEFAULT 'SYSTEM_AGENT';`
  - 使用 `ALTER TABLE archon_prompts ADD COLUMN metadata jsonb DEFAULT '{}'::jsonb;`
- **[NEW]** `migration/0.2.2/31_seed_art_asset_prompts.sql`
  - 將 `Art_Asset_Prompts.md` 的所有咒語轉化為 SQL `INSERT` 語句。

### 2. 🐍 Python Backend (FastAPI & Pydantic)
- **[NEW]** `python/src/server/schemas/prompts.py`
  - 建立嚴格的 Pydantic 型別防護：`PromptMetadata`, `PromptResponse`, `PromptUpdateRequest`。
- **[MODIFY]** `python/src/server/api_routes/prompts_api.py`
  - 路由綁定 `response_model=list[PromptResponse]`。
  - 將 Request Body 從 `content: dict[str, str]` 升級為強型別的 `PromptUpdateRequest`。
- **[MODIFY]** `python/src/server/services/prompt_service.py`
  - 擴充 CRUD 邏輯以支援存取與更新 `category` 和 `metadata`。

### 3. 📝 Documentation
- **[MODIFY]** `recontextualization/docs/Art_Asset_Prompts.md`
  - 清空舊有冗長內容，改為宣告已遷移至 SSOT，引導使用者至 5173 UI 進行管理。

# Phase 5.11.2: Presentation Agent Hardening & SSOT Resolution

## 1. 核心目標 (Core Objectives)
徹底根除 `PresentationAgent` 開發初期遺留的「樂觀路徑 (Optimistic Paths)」、「硬編碼 (Hardcoding)」與「架構斷層 (Architectural Gaps)」，將其提升至符合 Archon 生產環境標準的強健架構。嚴格落實 SSOT 原則，禁止任何短期虛假開發 (Fake Development)。

## 2. 深度 Code Review 發現之斷層與未爆彈 (Identified Gaps)

### 2.1 60 分鐘 OAuth Token 未爆彈 (The 60-Minute Token Timebomb)
*   **檔案位置**: `python/src/mcp_server/features/google_drive/gdrive_tools.py`
*   **錯誤邏輯**: `creds = Credentials(token=token)`
*   **斷層說明**: 目前的實作僅接受單一的 OAuth Access Token。Google 的 Access Token 壽命精準為 3,600 秒 (1 小時)。如果直接將此 Token 寫入 `.env`，系統將在 60 分鐘後穩定觸發 `401 Unauthorized` 錯誤。這是不顧未來維護的虛假開發。

### 2.2 筆記本 ID 硬編碼斷層 (Notebook ID Hardcoding)
*   **檔案位置**: `python/src/server/services/agents/dispatcher.py` (約行 210)
*   **錯誤邏輯**: `"notebook_id": "default-notebook"`
*   **斷層說明**: 強制將目標筆記本設為 `"default-notebook"`，未從 UI 或任務元資料 (Task Metadata) 動態讀取。如果該筆記本不存在，或使用者希望指定不同筆記本，任務將直接失敗。此為經典的「樂觀路徑」假設。

### 2.3 動態任務路由與依賴對齊 (Dynamic Metadata Routing)
*   **檔案位置**: `python/src/server/services/agents/dispatcher.py` & `presentation_agent.py`
*   **斷層說明**: 目前缺乏對 `due_date` 與自訂參數 (如 `drive_folder_id`) 的有效萃取，導致後端 API 無法靈活處理不同使用者的客製化輸出需求。

## 3. 解決方案與實作計畫 (Architecturally Correct Solutions)

### 3.1 基礎設施重構：OAuth Refresh Token 自動展期 (保留 Gmail 登入)
**行動計畫**:
1. **捨棄複雜的 Service Account**：考量到系統部署於 Hugging Face (HF) 且使用者透過 5173 登入，要求使用者設定共用資料夾的 UX 過於複雜。我們將維持您原本的期望：**直接使用您的 Gmail 帳號**。
2. **解決 60 分鐘過期問題**：
   * 不再只依賴短效期的 `Access Token`。
   * 我們需要在 HF 的 Secrets (或 Supabase 環境變數) 中，補齊 `REFRESH_TOKEN`, `CLIENT_ID`, 與 `CLIENT_SECRET`。
3. **實作細節 (免開發新 UI)**：
   * 修改 `gdrive_tools.py`，傳入這三個參數。
   * Google SDK 會在背景自動利用 `refresh_token` 無限期展期 (Auto-refresh)。
   * 如此一來，HF 上的後端機器人就能以您的 Gmail 身分永久上傳檔案，完全不需要在 5173 開發任何新的登入介面，且徹底拆除了 60 分鐘未爆彈。

### 3.2 拔除硬編碼：動態讀取 Task Metadata
**行動計畫**:
1. 修改 `dispatcher.py` 中的 `PresentationStrategy`。
2. 將硬編碼改為動態萃取：
   ```python
   metadata = task_data.get("metadata", {})
   notebook_id = metadata.get("notebook_id")
   drive_folder_id = metadata.get("drive_folder_id")
   if not notebook_id:
       raise ValueError("Task metadata is missing 'notebook_id'.")
   ```
3. 導入 Fail-Fast 機制：如果必填參數缺失，立即中斷任務並記錄錯誤，絕不盲目執行。

### 3.3 強化工作流程：強制 due_date 檢查
**行動計畫**:
1. 在 UI 文件或專案管理規範中，明確宣告 AI 生成任務 (尤其是排程或簡報生成) 應設定 `due_date`。
2. 於 `create_logic.py` 或 Task 介面增加防呆檢查或日誌提醒，確保所有 Agent 任務的生命週期可被 `TaskDispatcher` 正確追蹤與排程。

## 4. 驗收標準 (Acceptance Criteria)
- [ ] `gdrive_tools.py` 不再依賴短效期的 Access Token，成功使用 Service Account JSON 進行實體驗證上傳。
- [ ] `dispatcher.py` 中不存在 `"default-notebook"` 字串，確實從任務 metadata 中解析參數。
- [ ] 全域模型 SSOT (`PRESENTATION_AGENT_MODEL`) 維持指向 `SYSTEM_MODELS`，沒有任何自訂模型環境變數散落在 `.env` 中。

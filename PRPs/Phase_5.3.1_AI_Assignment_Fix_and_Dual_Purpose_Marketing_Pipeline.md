# Phase 5.3.1: 任務指派與通知機制修復暨數位孿生錄影行銷素材聯動計畫

## 📋 核心願景與 5.3.1 增訂目的
本計畫繼承並演進了 Phase 5.3.0 的核心願景（外部生成概念影片 Intro + 本地側錄操作影片 Body ➡️ 匯入 RAG 知識庫 ➡️ 前端行銷工作台 Bob 聯動播放）。

**在 5.3.1 中，我們特別針對以下兩項導致自動化驗收流程卡死的「任務指派與通知機制 Bug」進行正本清源的修復：**
1. **任務建立之 Due Date 缺失**：
   在任務 Modal [TaskModal.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/components/TaskModal.tsx) 中，截止日期（Due Date）為前端 required 必填欄位。原先的 `twin_scout.py` 在建立任務時漏填了此欄位，導致前端 Alert 彈窗阻擋提交，任務根本沒有送出。我已在 Playwright 步驟中加入了對日期選單 [MobileDateTimePicker](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/components/common/MobileDateTimePicker.tsx) 的自動化點選與提交。
2. **AI Assignee 匹配失效與 UUID 傳遞錯誤**：
   後端 `ops.py` 建立任務時，為了繞過外鍵限制會把 `assignee_id` 清空為 `None`，並將 `assignee` 改為單字切片後的 `"Supervisor"`（而非原始完整的 `"Supervisor (Group Chat)"`）。
   而在 `create_logic.py` 與 `update_logic.py` 中，原始碼使用 `assignee in AI_AGENT_ROLES` 進行比對。由於 `"Supervisor" in AI_AGENT_ROLES` 為 False，導致系統判定這不是 AI 任務，**完全沒有發送 AI 任務通知，任務直接卡死在 todo 狀態，無法被背景 WorkerService 執行，因而前端加載不出 AI Report**。
   我們在此處修復為**前綴/子字串容錯匹配**，並傳遞正確的 **AI Agent UUID**，從根本上解決任務無法觸發執行的問題。

---

## 🔍 技術標準與邊界限制
1. **前綴匹配與 UUID 映射**：
   在任務建立或更新時，若 `assignee` 欄位符合 `AI_AGENT_ROLES` 任何角色名稱的前綴或子字串，即判定其為 AI 任務。透過角色匹配將對應的真實 UUID（如 `AgentUUIDs.SUPERVISOR`）注入到 `_notify_ai_agent_of_assignment` 函數。
2. **互動式自癒日期點選**：
   透過 Playwright 點選日期組件，並確認選擇。
3. **前端播放器合規 (UI_STANDARDS.md 合規)**：
   * 使用靜態類別配置播放器樣式。
   * 為播放按鈕與 RAG 引用 Popover 加上 `aria-label`、`aria-pressed` 及 `aria-expanded`。

---

## 🛠️ 具體實作步驟 (Actionable Plan)

### 第一步：後端 AI 任務指派匹配修復
*   **目標檔案**: 
    *   `python/src/server/services/projects/tasks/create_logic.py` [MODIFY]
    *   `python/src/server/services/projects/tasks/update_logic.py` [MODIFY]
*   **實作細節**:
    *   在任務建立和更新邏輯中，引入 `AI_AGENT_ROLES` 的前綴/子字串匹配：
        ```python
        agent_id = None
        if assignee_id in AI_AGENT_ROLES.values():
            agent_id = assignee_id
        else:
            for name, aid in AI_AGENT_ROLES.items():
                if assignee and (name.startswith(assignee) or assignee in name):
                    agent_id = aid
                    break
        ```
    *   確保通知 MCP 時，傳遞的必定是此匹配到的 `agent_id`（UUID）。

### 第二步：Playwright 由於截止日期 (Due Date) 之點選注入
*   **目標檔案**: `scripts/twin_scout.py` [MODIFY]
*   **實作細節**:
    *   在新建任務表單時，自動定位 `#date-picker-due-date` 並點擊。
    *   點選 Tomorrow 快速鍵，並點擊 `CONFIRM SELECTION` 保存截止日期，確保表單能繞過前端驗證成功提交。

### 第三步：外部素材自動生成與下載 (Intro/Outro) *(已完成)*
*   **目標檔案**: `scripts/generate_gemini_intro.py` [NEW]

### 第四步：自動化後處理與轉檔
*   **目標檔案**: `scripts/process_marketing_video.py` [NEW] *(已完成)*

### 第五步：前端 UI 影片播放整合 *(已完成)*
*   **目標檔案**: 
    - `EditorBody.tsx` (行銷編輯器 workbench) [MODIFY]
    - `RAGCitation.tsx` (RAG 引用彈窗) [MODIFY]
    - `SourceContextPane.tsx` (側邊欄 Context 卡片) [MODIFY]

---

## ⚠️ 前置風險評估 (Pre-Action Assessment)
1. **熱重載死結風險**：
   修改 python 檔案會觸發 Uvicorn 重載，此時不可立即跑 E2E 測試，必須確保重載完成（或手動重啟容器）且 `/health` 探針能秒回 200 OK，方能執行巡航。

# Phase 3.9: AI 即隊友 PoC 計畫書

## 1. 核心理念與動機 (Vision & Motivation)

根據我們的討論，Phase 3.9 的核心目標是實現 **「AI 即隊友 (AI as a Teammate)」** 的協作願景。

此舉的動機源於一個深刻的洞察：現實世界中的團隊協作充滿挑戰，人類同事的效率和可用性難以預測。本計畫旨在透過引入可靠、可追蹤、且效率極高的 **AI 隊友**，來增強現有團隊的能力，打造一個更高效、更透明的工作環境。

本文件將闡述第一個概念驗證 (PoC) 的具體實施步驟。

## 2. 概念驗證 (PoC) 開發計畫

**PoC 核心流程**: 使用者在 `enduser-ui-fe` 中建立一個新任務，將其指派給「設計師 AI」。後端模擬 AI 完成工作，並在任務下方「貼出」一張由 AI 生成的圖片。

**具體實施步驟**:

1.  **後端 API 升級: `GET /api/assignable-users`**
    *   **目標**: 使「指派」功能同時兼容人類與 AI Agent。
    *   **待辦**: 修改 `python/src/server/api_routes/projects_api.py` 中的 `get_assignable_users` 函式。
    *   **規格**: 除了查詢 `profiles` 資料表中的人類使用者外，需額外加入一個寫死的 AI Agent 列表。最終回傳兩者的合併列表。
    *   **範例程式碼**:
        ```python
        # python/src/server/api_routes/projects_api.py
        # ... inside get_assignable_users ...
        ai_agents = [
            {'id': 'agent-designer-01', 'name': '設計師 AI', 'role': 'AI_AGENT'},
            {'id': 'agent-knowledge-01', 'name': '知識庫 AI', 'role': 'AI_AGENT'},
        ]
        # ... (既有的 user 查詢邏輯) ...
        return users_from_db + ai_agents
        ```

2.  **前端類型定義: `AssignableUser`**
    *   **目標**: 讓前端的 TypeScript 能夠識別 AI Agent。
    *   **待辦**: 修改 `enduser-ui-fe/src/types.ts`。
    *   **規格**: 為 `AssignableUser` 類型增加 `role` 欄位，並納入 `'AI_AGENT'`。
    *   **範例程式碼**:
        ```typescript
        // enduser-ui-fe/src/types.ts
        export interface AssignableUser {
          id: string;
          name: string;
          role: 'MEMBER' | 'SYSTEM_ADMIN' | 'AI_AGENT'; // 新增 AI_AGENT
        }
        ```

3.  **前端介面升級: 智慧指派選單**
    *   **目標**: 在 UI 上視覺化地區分人類與 AI。
    *   **待辦**: 修改 `enduser-ui-fe/src/components/TaskModal.tsx` 中的指派選單。
    *   **規格**: 在渲染下拉選單選項時，檢查 `user.role`。如果角色是 `AI_AGENT`，則在名稱旁顯示一個「機器人」圖示。
    *   **範例程式碼 (概念)**:
        ```tsx
        // enduser-ui-fe/src/components/TaskModal.tsx
        {assignableUsers.map(user => (
          <SelectItem key={user.id} value={user.id}>
            <div className="flex items-center">
              {user.role === 'AI_AGENT' 
                ? <BotIcon className="mr-2" /> 
                : <UserIcon className="mr-2" />}
              <span>{user.name}</span>
            </div>
          </SelectItem>
        ))}
        ```

4.  **前端介面升級: AI 產出渲染**
    *   **目標**: 讓 AI 的工作成果能直接顯示在 UI 上。
    *   **待辦**: 修改 `enduser-ui-fe/src/pages/DashboardPage.tsx` 中顯示任務附件的邏輯。
    *   **規格**: 在渲染附件列表時，檢查附件的 `file_name`。如果檔案是圖片格式 (如 `.png`, `.jpg`)，則直接渲染成 `<img>` 標籤，而不是一個普通的下載連結。
    *   **範例程式碼 (概念)**:
        ```tsx
        // enduser-ui-fe/src/pages/DashboardPage.tsx
        {task.attachments.map(attachment => (
           isImage(attachment.file_name)
             ? <img src={attachment.url} alt={attachment.file_name} />
             : <a href={attachment.url}>{attachment.file_name}</a>
        ))}
        ```

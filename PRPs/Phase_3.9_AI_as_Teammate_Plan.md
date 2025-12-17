# Phase 3.9: AI 即隊友 PoC 計畫書

## 1. 核心理念與動機 (Vision & Motivation)

根據我們的討論，Phase 3.9 的核心目標是實現 **「AI 即隊友 (AI as a Teammate)」** 的協作願景。

此舉的動機源於一個深刻的洞察：現實世界中的團隊協作充滿挑戰，人類同事的效率和可用性難以預測。本計畫旨在透過引入可靠、可追蹤、且效率極高的 **AI 隊友**，來增強現有團隊的能力，打造一個更高效、更透明的工作環境。

本文件將闡述第一個概念驗證 (PoC) 的具體實施步驟。

## 2. 概念驗證 (PoC) 開發計畫 v1.1

**與 `TODO.md` 的關係**: 本計畫是對 `TODO.md` 中「核心工作流程圖」的**第一階段實作**。我們將聚焦於讓前端具備「感知」並能「指派」任務給 AI 的能力，為後續 AI 的自主工作流程打下基礎。

**PoC 核心流程**: 使用者在 `enduser-ui-fe` 中建立一個新任務，根據其自身權限，在指派選單中看到可指派的人類與 AI。將任務指派給「設計師 AI」後，後端模擬 AI 完成工作，並在任務下方「貼出」一張由 AI 生成的圖片。

**具體實施步驟**:

1.  **後端 API 升級: `GET /api/assignable-users` (整合權限控管)**
    *   **目標**: 使「指派」功能**同時兼容人類與 AI Agent**，並嚴格遵守已定義的**權限規則**。
    *   **待辦**: 重構 `python/src/server/api_routes/projects_api.py` 中的 `get_assignable_users` 函式。
    *   **規格**:
        1.  此 API 必須透過 FastAPI 的依賴注入，獲取**當前發出請求的使用者** (`current_user`) 的角色資訊。
        2.  函式內部需實例化 `RBACService` (位於 `python/src/server/services/rbac_service.py`)。
        3.  獲取一份包含**所有**人類使用者和所有 AI Agents 的完整列表。
        4.  遍歷這份完整列表，使用 `rbac_service.has_permission_to_assign(current_user.role, target_user.role)` 進行過濾。
        5.  只回傳**當前使用者有權限指派**的人員列表給前端。
        6.  移除原有的靜態 AI 列表，改為從一個統一的配置或註冊表中讀取。
    *   **範例程式碼 (概念)**:
        ```python
        # python/src/server/api_routes/projects_api.py
        from ..services.rbac_service import RBACService # 導入 RBAC 服務
        
        # ... inside get_assignable_users(current_user: User = Depends(get_current_user)) ...
        
        rbac_service = RBACService()
        
        all_possible_assignees = get_all_humans() + get_all_ai_agents()
        
        allowed_assignees = [
            assignee for assignee in all_possible_assignees
            if rbac_service.has_permission_to_assign(current_user.role, assignee.role)
        ]
        
        return allowed_assignees
        ```

2.  **安全性與權限 (Security & Permissions)**
    *   **目標**: 將 `RBACService` 的規則作為後端 API 的「唯一事實來源」。
    *   **規格**:
        *   任何與「任務指派」相關的 API (`create_task`, `update_task`) 在儲存指派變更前，都**必須**再次呼叫 `rbac_service.has_permission_to_assign` 進行伺服器端驗證。
        *   此舉可防止惡意使用者透過手動修改 API 請求，繞過前端 UI 的限制，將任務指派給沒有權限的對象。

3.  **前端類型定義: `AssignableUser`**
    *   **目標**: 讓前端的 TypeScript 能夠識別 AI Agent。
    *   **待辦**: 修改 `enduser-ui-fe/src/types.ts`。
    *   **規格**: 為 `AssignableUser` 類型增加 `role` 欄位，並納入 `'AI_AGENT'` 以及其他所有人類角色。
    *   **範例程式碼**:
        ```typescript
        // enduser-ui-fe/src/types.ts
        export interface AssignableUser {
          id: string;
          name: string;
          // 確保 role 包含所有後端 RBACService 中定義的角色
          role: 'Admin' | 'PM' | 'Engineer' | 'Marketer' | 'AI_AGENT' | 'SYSTEM_ADMIN'; 
        }
        ```

4.  **前端介面升級: 智慧指派選單**
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
                ? <BotIcon className="mr-2" /> /* 機器人圖示 */
                : <UserIcon className="mr-2" /> /* 人類圖示 */}
              <span>{user.name}</span>
            </div>
          </SelectItem>
        ))}
        ```

5.  **前端介面升級: AI 產出渲染**
    *   **目標**: 讓 AI 的工作成果能直接顯示在 UI 上。
    *   **待辦**: 修改 `enduser-ui-fe/src/pages/DashboardPage.tsx` 中顯示任務附件的邏輯。
    *   **規格**: 在渲染附件列表時，檢查附件的 `file_name`。如果檔案是圖片格式 (如 `.png`, `.jpg`)，則直接渲染成 `<img>` 標籤，而不是一個普通的下載連結。
    *   **範例程式碼 (概念)**:
        ```tsx
        // enduser-ui-fe/src/pages/DashboardPage.tsx
        {task.attachments.map(attachment => (
           isImage(attachment.file_name)
             ? <img src={attachment.url} alt={attachment.file_name} className="max-w-xs rounded" />
             : <a href={attachment.url} target="_blank">{attachment.file_name}</a>
        ))}
        ```

6.  **測試與驗證計畫 (Testing & Verification Plan)**
    *   **目標**: 確保 Phase 3.9 的前端新功能有自動化測試覆蓋，提高程式碼品質並防止未來的變更破壞既有功能。
    *   **方法**: 採用 `enduser-ui-fe` 專案已配置的 **Vitest** 與 **React Testing Library** 編寫元件測試 (Component Tests)。
    *   **測試案例 1: `TaskModal.test.tsx`**
        *   **目的**: 驗證「智慧指派選單」能正確渲染 AI Agent。
        *   **步驟**:
            1.  模擬 (Mock) `api.getAssignableUsers` 的回應，使其回傳一個包含人類和 AI Agent 的使用者列表 (例如，`{ id: 'ai-01', name: '設計師 AI', role: 'AI_AGENT' }`)。
            2.  渲染 `TaskModal` 元件。
            3.  斷言 (Assert) 下拉選單中，「設計師 AI」選項旁存在一個帶有特定測試 ID (如 `data-testid="ai-icon"`) 的圖示，而其他人類使用者則沒有。
    *   **測試案例 2: `DashboardPage.test.tsx`**
        *   **目的**: 驗證「AI 產出渲染」能正確顯示圖片。
        *   **步驟**:
            1.  建立一個包含兩種附件（一個是圖片 `report.jpg`，另一個是文件 `notes.pdf`）的假任務 (Mock Task)。
            2.  渲染 `DashboardPage` 或其子元件 `ListView`。
            3.  斷言頁面 DOM 中存在一個 `<img>` 標籤，其 `src` 屬性指向圖片 URL。
            4.  斷言頁面 DOM 中存在一個 `<a>` 標籤，其 `href` 屬性指向文件 URL。
    *   **執行**: 測試可透過在 `enduser-ui-fe` 目錄下執行 `pnpm test` 指令來運行，並可整合至 CI/CD 流程中。
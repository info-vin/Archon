# Archon 專案開發藍圖：Phase 2

本文件旨在規劃 Archon 專案的下一階段開發，核心目標是將 Agent 自動化與 RAG (檢索增強生成) 功能深度整合到 endUser-ui 中，實現人機協作的智慧任務管理。

## 1. 專案目標與使用案例 (Goals & Use Cases)

我們的目標是讓使用者（如專案經理、行銷人員）能透過 UI 介面，指派任務給 AI Agent，Agent 能利用知識庫或網路資源完成任務、產出文件，並自動更新任務狀態。

- **案例一：市場研究**
  - **使用者**: 專案經理 (PM)
  - **情境**: 為新客戶做產業背景研究。
  - **流程**: PM 在 UI 建立任務，要求 Agent 搜尋特定產業的挑戰與機會。Agent 完成後產出報告，並將任務狀態更新為「待審核」。

- **案例二：內部知識查詢**
  - **使用者**: 專案經理 (PM)
  - **情境**: 回覆客戶關於過去專案的技術細節問題。
  - **流程**: PM 指派 Agent 查詢指定的專案文件夾 (作為 KM)，Agent 從文件中找到答案、總結回覆，並更新任務狀態。

- **案例三：人機協作產出文件**
  - **使用者**: 行銷人員
  - **情境**: 製作一份行銷 DM。
  - **流程**: 行銷人員在 UI 建立任務，提供文案和需求，指派 Agent 進行後製。Agent 完成後將 DM 範例存檔，並將檔案連結附在任務中，最後更新任務狀態。

## 2. 預期專案架構 (Target Architecture)

為了支援上述案例，我們預期一個更完善的專案架構，包含前後端、資料庫和 Agent 的清晰分工。

```
/
├── endUser-ui-front/       # 前端應用
│   └── src/
│       ├── components/
│       │   └── ReportDashboard.tsx   # (新) 管理者儀表板組件
│       └── pages/
│           └── Dashboard.tsx         # (新) 儀表板頁面
│
├── python/                   # 後端應用
│   └── src/
│       ├── agents/
│       │   └── tools/
│       │       └── file_tools.py     # (新) Agent 的檔案處理工具
│       ├── server/
│       │   ├── api_routes/
│       │   │   ├── files_api.py      # (新) 處理檔案上傳的 API
│       │   │   └── reports_api.py    # (新) 儀表板數據的 API
│       │   └── services/
│       │       └── storage_service.py  # (新) 封裝與 Supabase Storage 互動的邏輯
│       └── ...
│
└── supabase/
    └── migrations/
        └── xxxx_add_customers_and_attachments.sql # (新) 資料庫遷移檔案
```

## 3. 核心工作流程圖 (Core Workflow Diagram)

下圖展示了使用者、前端、後端及 Agent 之間一次完整的任務協作流程：

```mermaid
graph TD
    subgraph "使用者 (User)"
        A[行銷人員]
    end

    subgraph "前端 (Frontend)"
        B[endUser-ui 介面]
    end

    subgraph "後端 (Backend)"
        C[Backend API]
        D[AI Agent]
        E[Supabase DB]
        F[Supabase Storage]
    end

    A -- 1. 建立/指派任務 --> B
    B -- 2. 呼叫 API (create/update task) --> C
    C -- 3. 觸發 Agent --> D
    C -- 4. 更新任務狀態 (todo ▶ progress) --> E
    E -- 5. Socket.IO 即時廣播 --> B
    D -- 6. 執行任務 (例如: 後製 DM) --> D
    D -- 7. 呼叫檔案上傳 API --> C
    C -- 8. 將檔案上傳至 --> F
    F -- 9. 回傳檔案 URL --> C
    C -- 10. 更新任務 (status: review, attachments: [URL]) --> E
    E -- 11. Socket.IO 即時廣播 --> B
    B -- 12. UI 自動更新 (任務移至 Review, 顯示連結) --> A
    A -- 13. 點擊連結審核檔案 --> F
```

## 4. 開發順序與待辦事項 (Development Plan)

我們將依賴關係，由後到前分階段進行開發：**後端基礎 -> Agent 能力 -> 前端功能**。

---

### **Phase 2.1: 後端基礎建設 (Backend Foundation)**

此為最高優先級，為所有新功能打下地基。

- **[ ] 資料庫擴充 (Database Schema)**
  - **目標**: 支援檔案附件和更多的資料實體。
  - **待辦**:
    1.  在 `archon_tasks` 資料表中，新增一個 `attachments` 欄位 (型別為 JSONB 或 TEXT[])，用來儲存檔案連結。
    2.  (可選) 新增 `customers` 和 `vendors` 資料表，並建立與 `projects` 的關聯。
    3.  建立一個新的 SQL 遷移檔案來執行上述變更。

- **[ ] 檔案上傳功能 (File Handling)**
  - **目標**: 讓 Agent 可以安全地儲存產出的檔案。
  - **待辦**:
    1.  在 `python/src/server/services/` 下建立 `storage_service.py`，專門處理與 Supabase Storage 的所有互動 (上傳、下載、取得 URL)。
    2.  在 `python/src/server/api_routes/` 下建立 `files_api.py`，提供一個 `POST /api/files/upload` 端點，接收檔案並使用 `StorageService` 進行上傳。

- **[ ] 核心 API 擴充 (Core API)**
  - **目標**: 讓任務可以關聯檔案。
  - **待辦**:
    1.  修改 `projects_api.py` 中的 `update_task` 邏輯，使其可以接收並更新 `attachments` 欄位。

---

### **Phase 2.2: Agent 能力擴充 (Agent Capabilities)**

在後端 API 備妥後，賦予 Agent 使用這些新功能的能力。

- **[ ] 開發 Agent 新工具 (Agent Tools)**
  - **目標**: 讓 Agent 能呼叫新的後端服務。
  - **待辦**:
    1.  在 `python/src/agents/tools/` 中建立 `file_tools.py`。
    2.  在其中定義一個 `upload_and_link_file_to_task` 工具，此工具會呼叫後端的 `POST /api/files/upload` 和 `PUT /api/tasks/{id}` 來完成檔案上傳與連結的完整流程。

- **[ ] 完善 Agent 工作邏輯 (Agent Logic)**
  - **目標**: 讓 Agent 能完整執行使用者指派的任務。
  - **待辦**:
    1.  修改或建立「行銷 Agent」、「PM Agent」，讓它們在工作流程的最後一步，使用 `upload_and_link_file_to_task` 工具來交付成果。

---

### **Phase 2.3: 前端功能開發 (Frontend Features)**

當後端和 Agent 都準備就緒後，開始進行使用者可見的功能開發。

- **[ ] 任務附件顯示 (Task Attachments)**
  - **目標**: 讓使用者可以在 UI 上看到並下載 Agent 產出的檔案。
  - **待辦**:
    1.  修改 `endUser-ui` 的任務詳情 (Task Details) 組件。
    2.  當任務資料中包含 `attachments` 欄位時，將其渲染成一個或多個可點擊的檔案連結。

- **[ ] 管理者儀表板 (Report Dashboard)**
  - **目標**: 提供一個給管理者的數據報告儀表板。
  - **待辦**:
    1.  **後端**: 在 `python/src/server/api_routes/` 下建立 `reports_api.py`，提供用於儀表板的數據聚合 API (例如 `GET /api/reports/task_summary`)。
    2.  **前端**: 在 `endUser-ui` 中建立新的儀表板頁面 (`/dashboard`) 和相關圖表組件 (`ReportDashboard.tsx`)。
    3.  **前端**: 呼叫新的報告 API，並將數據視覺化呈現（例如：各專案任務數量、狀態分佈圖等）。

---

---

## 5. 開發與測試策略 (Development & Testing Strategy)

為了確保專案的穩定性與程式碼品質，所有開發工作都應遵循以下策略。本策略是基於對專案既有測試框架的分析而定。

### 後端 (Python / Pytest)

1.  **禁止真實資料庫連線**: 所有單元/整合測試都**禁止**連線到真實的 Supabase 資料庫。測試環境會自動阻止這類網路請求。
2.  **使用模擬 (Mocking) 進行測試**:
    *   測試的核心是驗證商業邏輯，而非資料庫本身。
    *   必須使用 `conftest.py` 中提供的 `client` 和 `mock_supabase_client` 來進行測試。
    *   在測試的「Arrange (安排)」階段，明確設定 `mock_supabase_client` 的回傳值，以模擬資料庫的行為。
3.  **本地測試流程**:
    *   在 `python/` 目錄下執行 `pytest` 來快速驗證程式碼變更。
    *   在提交 (Commit) 程式碼前，必須確保所有本地測試都已通過。

### 前端 (React / Vitest)

1.  **模擬 API 呼叫**: 前端測試不應呼叫真實的後端 API。應使用 `msw` (Mock Service Worker) 或其他模擬工具來攔截 API 請求，並回傳預先定義好的假資料 (JSON)。
2.  **測試使用者互動**: 測試的重點應放在：
    *   元件是否根據傳入的 props 正確渲染。
    *   使用者的操作（如點擊、輸入）是否觸發了正確的函式。
    *   UI 狀態是否根據 API 的模擬回傳值或使用者操作而正確更新。
3.  **本地測試流程**:
    *   在 `endUser-ui-front/` 等前端專案目錄下執行 `npm test` (或 `yarn test`)。
    *   在提交 (Commit) 程式碼前，必須確保所有本地測試都已通過。

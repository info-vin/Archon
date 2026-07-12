# 後端 API 架構設計文件 (Backend API Architecture)

**適用對象**: 系統分析師 (SA)、後端開發者、AI Agent 架構師
**目的**: 作為後端 API 結構、服務交互與數據流的單一真理來源
**最後更新**: 2026-01-27
**語言**: 繁體中文 (Traditional Chinese)

---

## 1. 系統架構概觀 (System Overview)

Archon 的後端採用微服務化 (Microservice-like) 的模組設計，基於 **FastAPI** 框架，並深度整合 **Supabase** (PostgreSQL + Auth + Vector) 作為核心資料與身份驗證層。

### 系統模組目錄結構 (Directory Structure)

```text
### 雙前端 (Frontend Apps)
enduser-ui-fe/ (Admin UI - Port 5173)
└── src/features/admin/
    ├── components/PromptManagement.tsx  # Prompt 管理介面
    └── machines/promptMachine.ts        # XState 狀態機

archon-ui-main/ (EndUser App - Port 3737)
└── src/features/

### 後端 (Backend - Port 8181)
python/src/server/
├── api_routes/
│   └── system_api.py      # /api/system/prompts 等系統路由
└── services/
    └── system_service.py  # 處理 public.archon_prompts
```

### 核心服務交互圖 (Service Interaction)

```mermaid
graph LR
    %% Define Styles
    classDef frontend fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#fff;
    classDef backend fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff;
    classDef gateway fill:#8b5cf6,stroke:#7c3aed,stroke-width:2px,color:#fff;
    classDef database fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff;
    classDef external fill:#6b7280,stroke:#4b5563,stroke-width:2px,color:#fff;

    subgraph ClientLayer ["🖥️ Client Layer"]
        direction TB
        AdminUI["Admin UI (Port 5173)"]:::frontend
        EndUserUI["EndUser App (Port 3737)"]:::frontend
        Client["外部 API Client"]:::external
    end

    Gateway["API Gateway / Router"]:::gateway

    subgraph BackendLayer ["⚙️ Backend Layer (Port 8181)"]
        direction TB
        Auth["Auth Service"]:::backend
        Projects["Project Service"]:::backend
        Know["Knowledge Service"]:::backend
        Mkt["Marketing Service"]:::backend
        Agents["Agent Service"]:::backend
        Sys["System Service"]:::backend
    end

    subgraph Infrastructure ["🗄️ Infrastructure"]
        direction TB
        DB[("Supabase (PostgreSQL)")]:::database
        Vector[("Supabase (Vector)")]:::database
        LLM["LLM Providers (OpenAI/Gemini)"]:::external
        Crawlers["Crawler Service"]:::external
    end

    %% Client to Gateway
    AdminUI & EndUserUI & Client -- HTTPS --> Gateway
    
    %% Gateway to Microservices
    Gateway --> Auth & Projects & Know & Mkt & Sys
    
    %% Service Interactions
    Projects -- Async --> Agents
    Know -- Queue --> Crawlers
    Mkt -- RAG --> Vector
    Agents -- Tools --> LLM
    Agents -- "GitBranch" --> Agents
    
    %% Database Connections
    Auth & Projects & Know & Mkt & Sys --> DB
```

---

## 2. 身份驗證與安全規範 (Authentication & Security)

系統採用 **雙重驗證機制 (Dual Authorization Strategy)**，結合 JWT 標準與角色存取控制 (RBAC)。

### 2.1 驗證流程 (Auth Flow)
*   **Token**: 使用 Supabase 簽發的 JWT (`access_token`)。
*   **傳遞方式**: HTTP Header `Authorization: Bearer <token>`。
*   **開發後門**: 本地開發環境可使用 `/api/auth/dev-token` 快速獲取 Admin 權限。

### 2.2 角色存取控制 (RBAC)
系統定義了以下核心角色，權限矩陣由 `RBACService` 統一管理：

*   **System Admin**: 全系統最高權限。
*   **Admin**: 組織管理員，可管理使用者。
*   **Manager**: 部門主管，可審核內容與指派任務。
*   **Member**: 一般成員 (Sales, Marketing, Content Creator)。
*   **Viewer**: 僅讀權限。

**SA 注意事項**:
*   API 層會在 Header 注入 `X-User-Role` (來自 Gateway 或 Middleware) 輔助判斷，但核心邏輯必須驗證 `current_user` 的 JWT claim。
*   敏感操作 (如 `promote_lead`, `approve_blog`) 必須在 Service 層進行二次 RBAC 檢查。

---

## 3. 核心業務流程 (Core Business Workflows)

### 3.1 銷售線索轉化流程 (Sales-to-Vendor)

描述從外部職缺看板爬取資料，轉化為銷售線索，最終晉升為供應商的過程。

```mermaid
sequenceDiagram
    participant Sales as Alice (Sales)
    participant API as Marketing API
    participant Job as JobBoard Service
    participant DB as Supabase (Leads)
    participant Lib as Librarian (RAG)
    participant Vendor as Supabase (Vendors)

    Sales->>API: GET /api/marketing/jobs?keyword=AI
    API->>Job: search_jobs("AI")
    Job-->>API: Job List (104/LinkedIn)
    API->>DB: identify_leads_and_save() (Auto)
    DB-->>Sales: Return Job List (Preview)

    Sales->>API: POST /leads/{id}/promote
    Note over Sales, API: 決定開發此客戶
    API->>DB: Check RBAC (Can Promote?)
    
    par Async Processing
        API->>Vendor: INSERT into vendors
        API->>DB: UPDATE leads SET status='converted'
        API->>Lib: archive_sales_pitch()
        Lib->>DB: Create Vector Embeddings (RAG Knowledge)
    end
    
    API-->>Sales: Success (Vendor Created)
```

### 3.2 知識庫構建與 RAG 流程 (Knowledge Pipeline)

描述如何從 URL 爬取並建立向量索引。

```mermaid
sequenceDiagram
    participant User
    participant API as Knowledge API
    participant Crawler as Crawler Service
    participant Tracker as Progress Tracker
    participant Storage as Document Storage
    participant Vector as Vector Store

    User->>API: POST /knowledge-items/crawl
    API->>Tracker: Initialize Progress (ID: uuid)
    API->>Crawler: Async Dispatch (Semaphore Controlled)
    API-->>User: Returns { progressId: "..." }

    loop Polling
        User->>API: GET /crawl-progress/{id}
        API->>Tracker: Get Status
        Tracker-->>User: { status: "crawling", progress: 45% }
    end

    Note over Crawler, Vector: Background Task
    Crawler->>Crawler: Fetch Pages (Max Depth)
    Crawler->>Storage: Store Raw HTML
    Crawler->>Storage: Extract Text & Code
    Storage->>Vector: Generate Embeddings (OpenAI/Gemini)
    Storage->>Tracker: Update Progress (100%)
```

### 3.3 RAG Pipeline (語意檢索與生成)

描述 RAG API (`/api/rag/query`) 接收請求後，進行向量檢索、重排與 LLM 生成的過程。架構上具備容災降階與重排機制。

```mermaid
sequenceDiagram
    participant FE as Frontend App
    participant API as RAG API
    participant RAG as RAG Service
    participant Vector as Vector Store (Supabase)
    participant Reranker as ONNX Reranker
    participant LLM as LLM Provider (Gemini/Ollama)

    FE->>API: POST /api/rag/query { query, source_ids }
    API->>API: 檢查權限 (TASK_READ_OWN)
    API->>RAG: perform_rag_query()
    RAG->>Vector: Vector Similarity Search
    Vector-->>RAG: 回傳 Top-K Document Chunks
    
    opt Reranker Phase (若啟用)
        RAG->>Reranker: 傳入 Query + Chunks 重新排序
        Reranker-->>RAG: 回傳高相關性 Chunks
    end

    RAG->>LLM: 注入 System Prompt + Chunks + User Query
    LLM-->>RAG: 生成最終回答
    RAG-->>API: 整理回答與參考文獻
    API-->>FE: 回傳 JSON { success, answer, references }
```

### 3.4 Prompt Manager 流程與機制 (Prompt Governance)

為達到 100% 的業務數據對齊與動態調整能力，系統實作了**資料庫驅動**的系統提示詞管理架構。

- **存儲層**: 所有 Agent 與系統的 Prompt 統一存放在 `public.archon_prompts` 資料表中，具備 `is_system_protected` 欄位以防非管理員誤改。
- **後端 API**: 由 `System Service` 提供 `/api/system/prompts`，支援獲取與更新，並在更新後主動使後端的 RAG/Agent 快取失效。
- **前端介面 (Admin UI - Port 5173)**:
  - 核心組件為 `PromptManagement.tsx`。
  - 使用 **XState 狀態機 (`promptMachine.ts`)** 來嚴格控制狀態的流轉 (例如：`FETCH_SUCCESS`、`SELECT_PROMPT`)，徹底解耦 UI 渲染與業務邏輯。
  - 透過 `opsApi` 直接與後端通訊，儲存後的 Prompt 會即時套用到所有背後運行的 Agent 上，無需重啟伺服器。

---

## 4. API 詳細規格 (Detailed API Specification)

### 4.1 專案管理模組 (Projects Module)
**Base Path**: `/api`

| Method | Endpoint | Description | Request Body | Response Model |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/projects` | 列出專案 (支援 ETag) | - | `List[Project]` |
| **POST** | `/projects` | 建立專案 (AI 輔助) | `CreateProjectRequest` | `Project` |
| **GET** | `/tasks` | 列出任務 (過濾器) | - | `Paginated[Task]` |
| **POST** | `/tasks` | 建立/指派任務 | `CreateTaskRequest` | `Task` |

#### 關鍵資料模型 (Data Models)

**CreateProjectRequest**
```json
{
  "title": "string (required)",
  "description": "string",
  "github_repo": "string",
  "pinned": "boolean",
  "technical_sources": ["source_id_1"],
  "business_sources": ["source_id_2"]
}
```

**CreateTaskRequest**
```json
{
  "project_id": "uuid (required)",
  "title": "string (required)",
  "assignee_id": "uuid (optional)",
  "due_date": "ISO8601",
  "priority": "high|medium|low",
  "knowledge_source_ids": ["source_ids"]
}
```

### 4.2 行銷與內容模組 (Marketing Module)
**Base Path**: `/api/marketing`

| Method | Endpoint | Description | Request Body | Response Model |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/jobs` | 搜尋職缺 (自動存 Lead) | `?keyword=...` | `List[JobData]` |
| **GET** | `/leads` | 獲取已存銷售線索 | - | `List[Lead]` |
| **POST** | `/leads/{id}/promote` | 晉升 Lead 為供應商 | `PromoteLeadRequest` | `Vendor` |
| **POST** | `/blog/draft` | AI 撰寫部落格草稿 | `DraftBlogRequest` | `DraftBlogResponse` |
| **POST** | `/approvals/{type}/{id}/{action}` | 審核內容 (Admin Only) | - | `Status` |

#### 關鍵資料模型 (Data Models)

**PromoteLeadRequest**
```json
{
  "vendor_name": "string (company name)",
  "contact_email": "string@example.com",
  "notes": "業務備註"
}
```

**DraftBlogRequest**
```json
{
  "topic": "string",
  "keywords": "string (comma separated)",
  "tone": "professional|casual"
}
```

### 4.3 知識管理模組 (Knowledge Module)
**Base Path**: `/api`

| Method | Endpoint | Description | Request Body | Response Model |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/knowledge-items/crawl` | 觸發爬蟲 | `KnowledgeItemRequest` | `CrawlStartResponse` |
| **GET** | `/crawl-progress/{id}` | 查詢爬蟲進度 | - | `BaseProgressResponse` |
| **POST** | `/documents/upload` | 上傳文件 | `FormData` | `UploadProgress` |
| **POST** | `/rag/query` | 執行 RAG 檢索 | `RagQueryRequest` | `RagResult` |

#### 關鍵資料模型 (Data Models)

**KnowledgeItemRequest**
```json
{
  "url": "https://example.com",
  "knowledge_type": "technical|marketing",
  "tags": ["tag1", "tag2"],
  "max_depth": 2,
  "extract_code_examples": true
}
```

**ProgressResponse**
```json
{
  "progressId": "uuid",
  "status": "crawling|processing|completed",
  "progress": 45.5,
  "message": "Processing page 5/10...",
  "details": {
    "pagesCrawled": 5,
    "totalPages": 10
  }
}
```

### 4.4 系統管理模組 (System Module)
**Base Path**: `/api/system`

| Method | Endpoint | Description | Request Body | Response Model |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/prompts` | 獲取全域系統提示詞 | - | `List[PromptData]` |
| **POST** | `/prompts/{promptName}` | 更新系統提示詞 | `UpdatePromptRequest` | `Status` |

#### 關鍵資料模型 (Data Models)

**UpdatePromptRequest**
```json
{
  "prompt": "string",
  "description": "string (optional)"
}
```

---

## 5. 前端整合架構 (Frontend Integration)

### 5.1 EndUser App (archon-ui-main, Port 3737)
此圖說明前端 (`api.ts` Service Layer) 如何對應後端路由。

```mermaid
classDiagram
    direction LR

    %% Frontend Service Layer
    class FrontendService {
        <<api.ts>>
        getTasks()
        promoteLead()
        draftBlogPost()
        crawlKnowledgeItem()
    }

    %% Functional Dependencies
    FrontendService ..> Auth_API : /api/auth
    FrontendService ..> Projects_API : /api/projects
    FrontendService ..> Marketing_API : /api/marketing
    FrontendService ..> Knowledge_API : /api/knowledge-items

    %% Classes for Context
    class Auth_API {
        verify_token()
        check_rbac()
    }
    class Projects_API {
        manage_kanban()
        handle_updates()
    }
    class Marketing_API {
        run_rag_generation()
        auto_save_leads()
    }
    class Knowledge_API {
        orchestrate_crawl()
        manage_vectors()
    }
```

### 5.2 Admin UI (enduser-ui-fe, Port 5173) - Prompt Manager 架構
Admin UI 採用 XState 作為狀態機驅動，分離了 UI 元件與業務邏輯，並直接透過 `opsApi` 與 `/api/system/prompts` 通訊。

```mermaid
classDiagram
    direction LR
    class PromptManagement {
        <<React Component>>
        +useMachine(promptMachine)
    }
    class promptMachine {
        <<XState>>
        +FETCH_SUCCESS
        +SELECT_PROMPT
    }
    class opsApi {
        <<enduser-ui-fe/src/services/api/ops.ts>>
        +getSystemPrompts()
        +updateSystemPrompt()
    }
    class System_API {
        <<python/src/server/api_routes>>
        POST /api/system/prompts
    }

    PromptManagement --> promptMachine : 驅動狀態
    promptMachine --> opsApi : API 請求
    opsApi ..> System_API : HTTP
```
# ProjectFlow 後端開發與架構文件

---

## 後端與資料庫架構規劃 v2.1

#### **1. 總體目標與策略**

*   **目標:** 建立一個以事件驅動 (Event-Driven) 和 API 優先為核心的整合平台，將 ProjectFlow 應用程式與未來可能整合的外部系統（如 Opcenter APS, UiPath, SAS Viya, Salesforce）無縫連接，最終形成統一的資源、時間與工作管理平台。
*   **策略:** 採用原子化串接策略，透過中央整合層（訊息佇列與 API 閘道）實現各系統間的鬆散耦合與即時協調。

#### **2. 資料庫設計 (根據新文件修訂)**

新文件強調了多系統整合和統一數據層的需求，這強化了我們使用 PostgreSQL 作為中央數據倉儲的決策，並要求我們的資料模型具備處理來自不同來源數據的能力。

*   **技術選型:** PostgreSQL + Prisma (維持不變)。
*   **新增/修訂的資料模型:**
    *   **`Task` 模型:** 為了與外部系統（如 Opcenter APS）的生產排程數據對齊，建議增加 `externalId` (用於存放來自外部系統的任務 ID) 和 `sourceSystem` (標示任務來源，如 'APS', 'MANUAL', 'UiPath') 欄位。
        ```prisma
        // ... (其他模型定義不變)

        model Task {
          id          String   @id @default(uuid())
          title       String
          description String?
          status      Status   @default(PENDING)
          priority    Priority @default(MEDIUM)
          dueDate     DateTime?
          createdAt   DateTime @default(now())
          updatedAt   DateTime @updatedAt

          project     Project  @relation(fields: [projectId], references: [id])
          projectId   Int

          createdBy   User     @relation("CreatedBy", fields: [createdById], references: [id])
          createdById Int

          assignee    User?    @relation("AssignedTo", fields: [assigneeId], references: [id])
          assigneeId  Int?

          // 新增欄位以支援外部系統整合
          externalId  String?  @unique // 來自外部系統的唯一ID
          sourceSystem String?  // 數據來源系統 (e.g., "OpcenterAPS", "UiPath")
        }

        // ... (其他列舉類型定義不變)
        ```
    *   **`User` 模型 (配合無密碼登入 - 臨時措施):**
        *   `password` 欄位改為可選：`password String?`。
        *   **警告：** 這是一個**僅限於開發和自動化測試階段**的臨時措施，目的是繞過密碼安全策略帶來的測試阻礙。在部署到生產環境前，**必須**恢復密碼加密儲存和驗證的機制。
    *   **`EventLog` 模型 (新增):** 為了實現事件驅動架構的可追溯性，建議新增一個日誌表，記錄系統間的事件流。
        ```prisma
        model EventLog {
          id          String    @id @default(uuid())
          source      String    // 事件來源系統 (e.g., "OpcenterAPS", "UiPath")
          eventType   String    // 事件類型 (e.g., "PRODUCTION_ANOMALY", "TASK_UPDATED")
          payload     Json      // 事件的詳細內容 (JSON 格式)
          createdAt   DateTime  @default(now())
        }
        ```

#### **3. 後端 API 設計 (v2.1)**

*   **核心框架:** Node.js + Express.js (維持不變)。
*   **認證流程 (無密碼調整 - 臨時措施):**
    *   `POST /api/auth/register`: 接收 `email` 和 `name`，在資料庫中創建一個沒有密碼的使用者。
    *   `POST /api/auth/login`: 接收 `email`，在資料庫中查找該使用者。如果存在，**直接生成並返回 JWT**，跳過密碼驗證。
        *   **安全警告：** 此簡化登入流程**極度不安全**，僅用於開發和測試。生產環境必須實施強大的密碼雜湊、驗證和安全儲存機制。
*   **事件驅動整合:**
    *   **訊息佇列:** 引入 **Apache Kafka** (如 PDF 文件建議) 或 RabbitMQ 作為事件匯流排 (Event Bus)。
    *   **整合服務:** 後端將包含一個專門的整合服務，負責：
        1.  監聽來自 Kafka 的事件（例如，從 Opcenter APS 發出的生產異常事件）。
        2.  根據事件內容，調用相應的內部服務或外部 API（例如，觸發 UiPath 流程來發送通知）。
        3.  將內部系統產生的事件（例如，使用者在我們的平台上創建了一個新專案）發佈到 Kafka，供其他系統（如 SAS Viya）消費。
        4.  將所有發佈和接收的關鍵事件記錄到 `EventLog` 資料表。

#### **4. 下一步實施建議**

1.  **更新 Prisma Schema:** 根據 v2.1 的定義，更新 `prisma/schema.prisma` 檔案。
2.  **執行資料庫遷移:** 執行 `npx prisma migrate dev` 來更新資料庫結構。
3.  **調整後端認證邏輯:** 修改後端 `server/index.js` 中的註冊和登入 API，以實現無密碼驗證。
4.  **開發 API 路由:** 根據上面定義的端點，在 Express 中建立對應的路由和控制器邏輯。
5.  **整合事件日誌:** 在關鍵的 API 操作中，加入將事件寫入 `EventLog` 資料表的邏輯。

---

## ProjectFlow 開發作業說明書 v2.2 (Linux 環境)

#### **1. UML 概念說明**

UML (Unified Modeling Language) 是一種標準化的圖形化建模語言，用於軟體系統的視覺化、建構、文件化和指定。雖然我無法直接繪製圖表，但我可以解釋在 ProjectFlow 專案中，哪些 UML 圖類型最為相關，以及它們會如何描述系統。

1.  **用例圖 (Use Case Diagram):**
    *   **目的:** 描述系統的功能需求，從使用者（或外部系統）的角度展示系統能做什麼。它關注的是「誰」使用系統以及「他們」能用系統做「什麼」。
    *   **在 ProjectFlow 中的應用:**
        *   **參與者 (Actors):** 使用者 (User)、專案經理 (Project Manager)、後端 API (Backend API)。
        *   **用例 (Use Cases):** 註冊使用者、登入系統、建立專案、管理專案成員、建立任務、更新任務狀態、指派任務、篩選任務、匯出資料等。
    *   **範例描述:** 一個用例圖會顯示一個「使用者」與「建立任務」用例之間的連線，表示使用者可以執行建立任務的功能。

2.  **類別圖 (Class Diagram):**
    *   **目的:** 描述系統的靜態結構，包括系統中的類別、它們的屬性、操作以及類別之間的關係（如關聯、繼承、聚合）。它直接對應到資料庫的資料模型。
    *   **在 ProjectFlow 中的應用:**
        *   **類別 (Classes):** `User`、`Project`、`Task`、`UsersOnProjects`。
        *   **屬性 (Attributes):** 例如 `User` 類別會有 `id`、`email`、`name`、`password`、`role` 等屬性。
        *   **關係 (Relationships):** 例如 `User` 和 `Project` 之間是多對多關係（通過 `UsersOnProjects` 關聯類別），`Project` 和 `Task` 之間是一對多關係。
    *   **範例描述:** 一個類別圖會顯示 `User` 類別與 `Task` 類別，`Task` 類別會有 `assigneeId` 屬性指向 `User` 的 `id`，表示任務被指派給某個使用者。

3.  **序列圖 (Sequence Diagram):**
    *   **目的:** 描述物件之間在特定用例中互動的時間順序，強調訊息的傳遞。它非常適合展示 API 呼叫和系統組件之間的協作流程。
    *   **在 ProjectFlow 中的應用:**
        *   **流程:** 使用者登入流程、建立任務流程、更新任務狀態流程。
    *   **範例描述 (使用者登入流程):**
        1.  **使用者** -> **前端應用**: 輸入 Email，點擊登入。
        2.  **前端應用** -> **後端 API**: 發送 `POST /api/auth/login` 請求 (包含 Email)。
        3.  **後端 API** -> **資料庫**: 查詢使用者資訊。
        4.  **資料庫** -> **後端 API**: 返回使用者資訊。
        5.  **後端 API** -> **前端應用**: 返回 JWT。
        6.  **前端應用** -> **使用者**: 導向主頁面。

4.  **組件圖 (Component Diagram):**
    *   **目的:** 描述系統的物理組件（如檔案、資料庫、可執行檔）以及它們之間的依賴關係。它提供系統的高層次架構視圖。
    *   **在 ProjectFlow 中的應用:**
        *   **組件 (Components):** 前端應用 (React App)、後端 API (Node.js/Express Server)、PostgreSQL 資料庫、Kafka 訊息佇列。
        *   **依賴關係:** 前端應用依賴後端 API，後端 API 依賴 PostgreSQL 和 Kafka。

#### **2. ProjectFlow 開發作業說明書 v2.2 (Linux 環境)**

這份說明書旨在為開發者提供一個清晰、結構化的指南，以便在 Linux 環境下進行 ProjectFlow 的開發。

---

### **ProjectFlow 開發作業說明書 v2.2 (Linux 環境)**

#### **1. 專案概覽**

*   **簡介:** ProjectFlow 是一個基於 Web 的團隊任務管理應用程式，旨在幫助團隊協作、追蹤專案進度。它提供任務的建立、指派、狀態更新、篩選等功能。
*   **核心功能:**
    *   使用者註冊與登入 (開發測試階段為無密碼登入)。
    *   專案建立與管理。
    *   任務的 CRUD (建立、讀取、更新、刪除)。
    *   任務指派給團隊成員。
    *   任務狀態 (待辦、進行中、完成) 和優先級 (低、中、高) 管理。
    *   任務篩選與搜尋。
    *   多語言支援 (英、繁中、日、韓、越)。
    *   資料匯入/匯出。
*   **技術棧:**
    *   **前端:** React 19, TypeScript, Vite, Zustand (狀態管理), react-router-dom (路由), Tailwind CSS (樣式)。
    *   **後端:** Node.js, Express.js, TypeScript。
    *   **資料庫:** PostgreSQL (透過 Docker Compose 管理), Prisma (ORM)。
    *   **測試:** Vitest (單元測試), Playwright (E2E 測試)。
    *   **容器化:** Docker, Docker Compose。
    *   **訊息佇列 (未來擴展):** Apache Kafka。

#### **2. 開發環境設定 (Linux)**

本專案推薦使用 Docker Compose 啟動完整的開發環境，以確保跨平台的一致性。

*   **前提條件:**
    *   **Git:** 版本控制工具。
    *   **Node.js (LTS 版本):** 包含 npm (Node Package Manager)。
    *   **Docker:** 容器化平台。
    *   **Docker Compose:** 用於定義和運行多容器 Docker 應用程式的工具。

*   **克隆專案:**
    ```bash
    git clone https://github.com/info-vin/16x_imaus.git
    cd 16x_imaus/team-task-manager
    ```

*   **啟動開發環境 (推薦方式 - Docker Compose):**
    這是啟動前端、後端和資料庫的最簡單方式。
    ```bash
    # 在 team-task-manager 目錄下執行
    npm run dev:docker
    ```
    *   **說明:** 此命令會建置 Docker 映像檔（如果尚未建置）並啟動以下服務：
        *   `frontend`: 前端 React 應用程式 (通常在 `http://localhost:5173`)
        *   `backend`: 後端 Node.js/Express API 服務 (通常在 `http://localhost:3000`)
        *   `db`: PostgreSQL 資料庫實例。
    *   **停止環境:**
        ```bash
        # 在 team-task-manager 目錄下執行
        npm run stop:docker
        ```

*   **啟動開發環境 (替代方式 - 僅前端):**
    如果您只想開發前端，可以不使用 Docker Compose。
    ```bash
    # 在 team-task-manager 目錄下執行
    npm install   # 安裝前端依賴
    npm run dev   # 啟動前端開發伺服器 (通常在 http://localhost:5173)
    ```
    *   **注意:** 此方式不會啟動後端 API 和資料庫。

*   **資料庫設定 (PostgreSQL - 透過 Docker Compose):**
    當您運行 `npm run dev:docker` 時，PostgreSQL 資料庫會自動啟動。
    *   **資料庫連接:**
        *   **主機:** `localhost` (從主機連接) 或 `db` (從 Docker 容器內部連接)。
        *   **埠號:** `5434` (從您的電腦直接連接時使用), `5432` (在 Docker 內部網路，例如後端服務連接時使用)。
        *   **使用者:** `user`。
        *   **密碼:** `password`。
        *   **資料庫名稱:** `projectflow_db`。
    *   **Prisma 資料庫遷移:**
        當您修改 `prisma/schema.prisma` 檔案後，需要執行遷移來更新資料庫結構。
        ```bash
        # 在 team-task-manager/server 目錄下執行
        npx prisma migrate dev --name <migration_name>
        ```
        *   **注意:** 首次運行時，如果資料庫為空，Prisma 會自動建立所有表格。

#### **3. 常用開發指令 (Linux)**

在 `team-task-manager` 目錄下執行：

*   `npm install`: 安裝專案依賴。
*   `npm run dev`: 啟動前端開發伺服器。
*   `npm run build`: 建置前端生產版本。
*   `npm run lint`: 執行 ESLint 檢查程式碼風格和潛在錯誤。
*   `npm run format`: 使用 Prettier 自動格式化程式碼。
*   `npm run test`: 執行單元測試 (Vitest)。
*   `npm run test:e2e`: 執行端對端測試 (Playwright)。
*   `npm run dev:docker`: 啟動前端、後端和資料庫的 Docker Compose 環境。
*   `npm run stop:docker`: 停止 Docker Compose 環境。

#### **4. 程式碼結構**

*   `team-task-manager/src/`: 前端 React 應用程式的原始碼。
    *   `components/`: 可重用 UI 元件。
    *   `pages/`: 應用程式的各個頁面。
    *   `stores/`: Zustand 狀態管理 store。
    *   `i18n/`: 國際化相關配置和翻譯檔案。
    *   `types/`: TypeScript 類型定義。
    *   `utils/`: 通用工具函數。
    *   `legacy/`: 舊版 `DemoPage` 相關的程式碼。
*   `team-task-manager/server/`: 後端 Node.js/Express 應用程式的原始碼。
    *   `index.js`: 後端主入口檔案。
    *   `database.sql`: 資料庫初始化腳本。
    *   `prisma/`: Prisma ORM 相關檔案和資料庫 schema 定義。
*   `team-task-manager/public/`: 靜態資源檔案 (如圖片、翻譯檔案)。
*   `team-task-manager/docs/`: 專案文件，包括設計文件和資源。
*   `team-task-manager/design-docs/`: 結構化的設計文件。

#### **5. 開發流程**

*   **分支策略:**
    *   `main`: 生產環境穩定版本。
    *   `dev`: 開發主分支，所有新功能都從此分支切出，並最終合併回此分支。
    *   `feature/<feature-name>`: 為每個新功能或錯誤修復創建的獨立分支。
*   **提交規範:**
    *   使用清晰、簡潔的提交訊息。推薦使用 Conventional Commits 規範 (例如 `feat: add new user registration`, `fix: resolve task persistence bug`)。
*   **程式碼審查:**
    *   在將 `feature` 分支合併到 `dev` 之前，應進行程式碼審查。

#### **6. 測試**

*   **單元測試 (Unit Testing):**
    *   使用 Vitest 進行元件和工具函數的單元測試。
    *   運行命令: `npm run test`。
*   **端對端測試 (End-to-End Testing):**
    *   使用 Playwright 模擬使用者行為，測試整個應用程式流程。
    *   運行命令: `npm run test:e2e`。
    *   **注意:** 目前 `tests/` 目錄下的 E2E 測試是為舊版前端編寫的，可能需要根據 `dev` 分支的實際 UI 進行調整或重寫。

#### **7. 部署 (概念性)**

*   專案的前端和後端都可以被容器化為 Docker 映像檔，便於部署到任何支援 Docker 的環境（如 Kubernetes, AWS ECS, Google Cloud Run 等）。

#### **8. 故障排除**

*   **Docker 相關問題:**
    *   如果 `npm run dev:docker` 無法啟動，請檢查 Docker 是否正在運行。
    *   嘗試 `docker-compose down --volumes` 清理舊的容器和卷，然後再 `npm run dev:docker`。
    *   檢查 Docker 容器日誌：`docker-compose logs <service_name>`。
*   **npm 依賴問題:**
    *   嘗試 `npm cache clean --force` 後再 `npm install`。
    *   如果遇到 `package-lock.json` 衝突，請手動解決或刪除後重新 `npm install`。

--- 

#### **9. 後端 API 測試指南 (v2.1)**

本指南旨在說明如何測試基於 `v2.1` 架構文件實作的後端新功能，特別是**無密碼認證**和**事件日誌**。

*   **前提條件:**
    *   您的 Docker 環境正在運行 (`npm run dev:docker`)。
    *   後端伺服器可在 `http://localhost:3000` 訪問。
    *   您已使用新的 `database.sql` 重建了資料庫。

##### **步驟 1: 測試使用者註冊 (無密碼)**

打開一個新的終端機，使用 `curl` 發送 POST 請求來註冊一個新使用者。

```bash
curl -X POST http://localhost:3000/api/auth/register \
-H "Content-Type: application/json" \
-d '{"name": "testuser", "email": "test@example.com"}'
```

*   **預期結果:**
    您應該會收到一個包含 JWT token 的 JSON 回應，類似這樣：
    ```json
    {"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    ```

##### **步驟 2: 測試使用者登入 (無密碼)**

使用剛剛註冊的 email 進行登入。

```bash
curl -X POST http://localhost:3001/api/auth/login \
-H "Content-Type: application/json" \
-d '{"email": "test@example.com"}'
```

*   **預期結果:**
    您應該應該會收到一個包含 JWT token 的 JSON 回應。

##### **步驟 3: 驗證事件日誌**

現在，我們需要檢查資料庫，確認註冊和登入事件是否已成功記錄。

1.  **進入 Docker PostgreSQL 容器:**
    首先，找到您的資料庫容器名稱：
    ```bash
    docker ps
    ```
    在列表中找到 `team-task-manager-db-1` 或類似的名稱。然後執行以下命令進入 `psql`：
    ```bash
    # 將 <your_db_container_name> 替換為您實際的容器名稱
    docker exec -it <your_db_container_name> psql -U postgres -d task_manager_dev
    ```

2.  **查詢 `event_logs` 資料表:**
    在 `psql` 提示符 (`projectflow_db=#`) 後，輸入以下查詢：
    ```sql
    SELECT source, event_type, payload->>'email' as email FROM event_logs;
    ```

*   **預期結果:**
    您應該會看到一個包含兩筆記錄的表格，證明事件已成功寫入：
    ```
       source    |   event_type    |      email
    -------------+-----------------+------------------
     ProjectFlow | USER_REGISTERED | test@example.com
     ProjectFlow | USER_LOGGED_IN  | test@example.com
    (2 rows)
    ```

完成以上步驟，即可驗證後端 v2.1 的核心功能已正確實作。

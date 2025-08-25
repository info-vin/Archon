# Archon 專案待辦事項

## 環境設定 (Environment Setup)

- **待辦項目：設定必要的環境變數**
  - **目標**: 建立並填寫 `.env` 檔案，以供 Docker Compose 使用。
  - **方案**:
    1.  從 `.env.example` 複製一份名為 `.env` 的檔案。
    2.  在 `.env` 檔案中填入至少 `SUPABASE_URL` 和 `SUPABASE_SERVICE_KEY` 的值。
  - **原因**: 後端服務 (`archon-server`) 啟動時需要這些變數來連接資料庫，缺少會導致啟動失敗或功能異常。

## 後端 (Backend)

- **延後項目：為 API 加上基於角色的權限驗證**
  - **目標**: 限制設定相關 API (如 `/api/credentials`, `/api/settings`) 的存取權限。
  - **方案**:
    1.  定義新的管理員角色 (例如 `PROJECT_MANAGER`)。
    2.  在 FastAPI 的 API 路由函式中，加入權限檢查邏輯，只允許 `SYSTEM_ADMIN` 或 `PROJECT_MANAGER` 等授權角色存取。
  - **延後原因**: 等待相關業務流程確定後再進行實作。

## 前端 (Frontend)

- **待辦項目：實現 endUser-ui-front 到 archon-ui-main 的條件式連結**
  - **目標**: 在 `endUser-ui-front` 中，根據使用者角色，顯示一個可以另開視窗連結到 `archon-ui-main` 的選單項。
  - **方案**:
    1.  在導航組件中，使用 `useAuth` hook 獲取使用者角色。
    2.  如果角色為 `system_admin`，則渲染一個 `<a>` 標籤，`href` 指向 `archon-ui-main` 的位址，`target="_blank"`。
    3.  **注意**: 此方案需確保 `archon-ui-main` 有獨立的身份驗證機制。

- **待辦項目：為 endUser-ui-front 新增 Vite 代理設定**
  - **目標**: 讓 `endUser-ui-front` 在開發環境下能正確將 API 請求轉發到後端服務。
  - **方案**: 在 `endUser-ui-front/vite.config.ts` 中，加入 `server.proxy` 設定，將 `/api` 和 `/socket.io` 的請求指向後端位址。

## 開發工具 (Tooling & Scripts)

- **待辦項目：自動化 Mock Data 轉換為 SQL 種子檔案**
  - **目標**: 解決手動將前端 Mock Data 同步到資料庫的繁瑣問題。
  - **方案**:
    1.  讀取 `endUser-ui-front/src/services/api.ts` 檔案。
    2.  解析檔案內容，提取 `MOCK_EMPLOYEES`, `MOCK_PROJECTS` 等陣列資料。
    3.  將 JavaScript 物件轉換為 SQL `INSERT` 語句。
    4.  產生一個新的 SQL 檔案 (例如 `migration/seed_mock_data.sql`)，供開發者執行。
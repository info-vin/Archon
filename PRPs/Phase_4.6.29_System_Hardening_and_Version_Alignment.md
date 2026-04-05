# Phase 4.6.29: 系統硬化與版本對齊 (System Hardening and Version Alignment)

> **目標 (Goal)**: 
> 1. **消除環境雜音**：修正版本號回歸與過期的 API Key 顯示。
> 2. **物理對齊**：確保 3737 (Admin UI) 與 5173 (End-User UI) 看到的系統狀態與 `.env` 及 `migration/` 100% 一致。
> 3. **遷移優化**：解決 `MigrationService` 過度偵測歷史 SQL 檔案導致的偽陽性警告。

## 1. 物理修改清單 (Action Items)

- [x] **Task A: 版本號動態化 (Dynamic Versioning)**
    - **修改**: `python/src/server/config/version.py`。
    - **結果**: 實作動態偵測邏輯，優先掃描 `migration/` 目錄。已解決 Docker 內的路徑斷層。
- [x] **Task B: 104 Crawler 物理屏蔽 (Crawler Key Isolation)**
    - **修改**: `scripts/init_db.py` 與 `python/src/server/services/credentials/manager.py`。
    - **結果**: 將 104 API 標記為 `is_system_protected`，Admin UI (3737) 已無法透過 API 獲取這些內部 Key。
- [x] **Task C: API Key 強制同步 (API Key Force Sync)**
    - **修改**: `scripts/init_db.py`。
    - **結果**: 每次 `make db-init` 都會強制將 `.env` 加密同步至 DB，解決了內容不對齊的問題。
- [x] **Task D: RAG 模型基準對齊 (RAG Baseline Alignment)**
    - **修改**: `migration/0.2.2/seed_rag_defaults.sql`。
    - **結果**: 將預設模型從 `gemini-1.5-flash` 升級為 `gemini-2.5-flash`。
- [ ] **Task E: 遷移掃描硬化 (Migration Scanning Hardening)**
    - **修改**: `python/src/server/services/migration_service.py`。
    - **目標**: 僅掃描當前版本目錄，忽略 `0.1.0`, `0.2.1` 等過期歷史資料夾，消除 3737 的遷移警告。

## 2. 驗證方法 (Verification)

- [x] **驗證 A**: 執行 `docker exec archon-server python -c "from src.server.config.version import ARCHON_VERSION; print(ARCHON_VERSION)"` -> 預期 `0.2.2`。
- [x] **驗證 B**: 登入 3737 Settings 頁面，確認 API Keys 列表中無 `CRAWLER_104` 相關項目。
- [x] **驗證 C**: 核對 Admin UI 顯示的 `GOOGLE_API_KEY` 末 4 碼與 `.env` 是否一致。
- [ ] **驗證 D**: 刷新 3737 "Database Migrations" 頁面，確認 `Pending Migrations` 數量歸零（或僅顯示當前版本的必要項）。

## 3. 預期結果
- 系統不再顯示誤導性的 `0.2.1` 版號。
- 遷移頁面不再顯示與 0.2.2 架構無關的舊版本補丁。
- 系統治理邊界（Bob vs Admin）獲得物理層面的強化。

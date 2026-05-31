# Phase 5.5.2: Tech Debt Elimination - God Object Refactoring

## 目標 (Objective)
消除因功能快速迭代而產生的「巨型物件 (God Objects)」技術債。將超過 400 行的核心服務檔案（特別是 `manager.py` 與 `content_handler.py`）進行深層次 L2 模組化拆分，以確保架構的單一職責原則 (SRP)、提高可維護性並降低認知負載。

## 背景 (Context)
透過 `phase-audit` 的巨型技術債掃描 (Monolith Patrol) 發現：
1. `python/src/server/services/credentials/manager.py` (423 行): 先前雖然已經進行過初步拆分 (Phase 4.6.47)，但隨著系統硬化與安全性功能的疊加，該模組再次膨脹。
2. `python/src/server/services/marketing/content_handler.py` (436 行): 承載了過多職責，包括銷售話術生成、視覺素材生成、部落格草稿、審批流程等。

## 執行計畫 (Execution Plan)

### 1. 拆解 `manager.py` (Credentials Service)
將 `manager.py` 進一步拆分為更細粒度的職責模組：
- [ ] 釐清並將 `provider` 相關邏輯完全下放至 `provider_configs.py`，或建立專屬的 Provider Manager。
- [ ] 將底層的 DB CRUD 操作（如 `load_all_credentials`, `get_credential`, `set_credential` 等）分離為 Repository 模式。
- [ ] 將 `manager.py` 簡化為負責協調 (Facade) 的輕量級入口。

### 2. 拆解 `content_handler.py` (Marketing Service)
將單一的 ContentHandler 拆分為領域特定的處理器：
- [ ] `blog_generator.py`: 負責部落格草稿 (`draft_blog`, `draft_from_leads`, `submit_blog`)。
- [ ] `visual_generator.py`: 負責視覺素材回退機制 (`generate_visual_asset`)。
- [ ] `approval_manager.py`: 負責審批流程 (`process_approval`, `get_pending_approvals`, `generate_reject_suggestion`)。
- [ ] `sales_pitch.py`: 負責銷售話術 (`generate_pitch`)。

### 3. 測試對帳與品質門禁 (Quality Gates)
- [ ] 執行 `make lint` 確保模組間引入 (Imports) 正確。
- [ ] 執行 `make test-be` 確認後端測試在重構後全數通過。
- [ ] （必要時）執行 `make audit-qa` 以全端公證此次重構不會破壞 E2E 工作流。

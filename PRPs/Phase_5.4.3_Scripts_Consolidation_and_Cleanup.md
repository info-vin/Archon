# Phase 5.4.3: 腳本重構、整併與過期檔案清理計畫 (Scripts Refactoring, Consolidation & Cleanup)

本計畫旨在針對目前專案中累積的 37 個腳本進行系統性的整理與重構。透過合併重複的初始化腳本、整併系統驗證腳本、將 Shell 腳本 Python 化以提升跨平台相容性、歸檔一次性診斷腳本，以提升專案的長期維護品質，並確保 `make tech-debt-audit` 無警告通過。

## 1. 執行摘要 (Executive Summary)
專案發展至今，在 `scripts/` 目錄下累積了多種性質的腳本（包括資料準備、驗證門禁、一次性偵錯等）。這導致了代碼重複率高（如 Supabase 連線初始化）以及部分腳本與平台相依（如 `.sh` 檔案在 Mac 與 Linux 的相容問題）。本階段將透過重構與整併，簡化腳本結構，並確保開發與 CI 流程調用路徑一致。

---

## 2. 資料安全性與 RAG 影響評估
* **安全無破壞性**：本次重構**不執行** `--clean` 重置指令，不影響現有的 RAG 知識庫與測試資料。
* **物理隔離與清理**：僅在 `17_drop_unused_tables.sql` 中移除確認已無任何業務與資料關聯的空白殭屍表，保留所有核心資料。

---

## 3. 具體重構內容

### 3.1 測試資料設定整合 (`setup_personas.py`)
將以下角色初始化腳本整合為單一進入點：
* `scripts/setup_alice_lead.py`
* `scripts/setup_bob_pitch.py`
* `scripts/setup_bob_report.py`
* `scripts/setup_charlie_approval.py`
* `scripts/setup_david_rbac.py`
* `scripts/setup_level_sandbox.py`

**新調用方式**：
```bash
python scripts/setup_personas.py --role [alice|bob|charlie|david|sandbox|all]
```

### 3.2 驗證腳本整合 (`verify_system.py`)
整併多個零散的驗證腳本：
* `scripts/verify_migrations.py`
* `scripts/verify_david_evolution.py`
* `scripts/verify_librarian_hunter.py`
* `scripts/verify_mcp_health.py`

**新調用方式**：
```bash
python scripts/verify_system.py --check [migrations|mcp|evolution|librarian|all]
```

### 3.3 Shell 腳本 Python 化
將原平台相依的 Shell 腳本改寫為 Python 版本，確保在 Mac 本地與 Linux 容器環境下運作一致：
* `scripts/find_large_files.sh` ➜ `scripts/find_large_files.py`
* `scripts/find_unused_ts.sh` ➜ `scripts/find_unused_ts.py`
* `scripts/probe_dns_leak.sh` ➜ `scripts/probe_dns_leak.py`

### 3.4 舊腳本歸檔
將一次性偵錯或已不使用的舊腳本物理移入 `scripts/archive/`。
* `test_gemini_manga.py`
* `test_embedding_upgrade.py`
* `approve_verify.py`
* `inspect_headers.py`
* `query_logs.py`

### 3.5 Makefile 路徑更新
同步更新 `Makefile` 中所有對應的調用指令（例如 `make audit-qa` 等），使其指引至重構後的新路徑。

---

## 4. 驗證計畫 (Verification Plan)
1. **執行 `make db-init`**：驗證遷移與種子資料在非破壞性執行下是否運作正常。
2. **執行 `make tech-debt-audit`**：驗證 stale 警告是否成功完全消除。
3. **執行 `make audit-qa`**：確保系統重構後，所有靜態、單元與流程門禁均能通過。

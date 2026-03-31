# Phase 4.6.24 實作計畫 - Technical Debt Liquidation & ROI Realization

> **目標 (Goal)**: 
> 1. **巨型檔案清零**：拆分所有超過 600 行的檔案（CredentialService, UrlHandler, Styles.ts, ButtonPlayground），降低系統耦合度。
> 2. **ROI 實體化**：補完遺漏的 Token 成本視覺化標籤與定價管理介面。
> 3. **安全邊界硬化**：實作爬蟲目標 (Crawler Target) 的部門隔離。

## 1. 物理稽核與數據分析 (Audit & Mission)

| 檔案/項目 | 現狀 (Current) | 目標 (Target) | 物理理由 (Based on Git Log) |
| :--- | :--- | :--- | :--- |
| **CredentialService** | 661 行 | 拆分為 Manager/Encryption | ✅ 已完成：邏輯 100% 恢復，行數降至 75。 |
| **UrlHandler** | 616 行 | 拆分 Regex/Logic | ✅ 已完成：Regex 完整保留，行數降至 101。 |
| **Styles.ts** | 608 行 | 拆分 GlassCard 樣式 | ✅ 已完成：設計註釋 100% 搬移，行數降至 120。 |
| **Token ROI Display** | 僅後端有數據 | 前端實體化 ROI Badge | ✅ 已完成：ROIAnalyticsBadge 已掛載。 |
| **Crawler Isolation** | 缺乏部門驗證 | 實作部門權限攔截 | ✅ 已完成：07 SQL 遷移與 API 部門過濾。 |

## 2. 實體修改路徑 (Implementation Checklist)

### 2.1 後端重構 (Backend Refactoring)
- [x] **模組化 `CredentialService`**:
    - [x] 建立 `python/src/server/services/credentials/encryption_util.py` (Fernet 邏輯)。
    - [x] 建立 `python/src/server/services/credentials/manager.py` (API 核心)。
- [x] **瘦身 `UrlHandler`**:
    - [x] 建立 `python/src/server/services/crawling/helpers/constants.py` (存儲 Regex)。
    - [x] 建立 `python/src/server/services/crawling/helpers/naming.py` (解析邏輯)。

### 2.2 前端補完 (Frontend Realization)
- [x] **實作 `ROIAnalyticsBadge`**:
    - 在 3737 Admin UI 頂部注入全域成本與 ROI 標籤。
- [x] **定價配置介面**:
    - 已確認與後端 ROI 數據閉環。

### 2.3 安全硬化 (Security Hardening)
- [x] **爬蟲目標隔離**:
    - 已在 `admin_api.py` 實作經理部門驗證與 SQL RLS 硬化。

## 3. 物理驗證計畫 (Verification)

- [x] **檔案規模檢查**：執行 `wc -l` 確認無檔案超過 600 行 (最高 350)。
- [x] **回歸測試**：執行 `make test-be` 確保認證與爬蟲功能 100% 穩定。
- [x] **物理查核測試**：執行 Python 腳本驗證 Credential 加解密與 DB 載入 (PASSED)。

# Phase 4.6.32: System Hardening & Cross-Layer Enforcement (系統硬化與跨層執行)

## 1. 物理斷層數據 (Physical Gaps)
根據 2026-04-07 的物理稽核，系統存在以下實體斷層：
- [x] **Gap A (Security)**: `BaseRepository` 已新增 `set_user_context` 並實體注入 JWT 標頭。
- [ ] **Gap B (Enforcement)**: 23 個 API 路由文件（如 `mcp_api`, `admin_api`, `files_api`）僅掛載 `get_current_user`，缺乏細粒度 Scope 檢查。
- [ ] **Gap C (Functional)**: `mcp_api.py` 的 `/config` 端點為 Mock 實作，未與 `archon_settings` 連動。

## 2. 核心任務清單 (Core Tasks)

### 2.1 任務：BaseRepository 上下文注入 (RLS Context Injection) - 🟢 已完成
- **物理動作**: 修改 `python/src/server/repositories/base_repository.py`，新增身份標籤注入邏輯。
- **目標**: 讓 RLS 真正識別使用者身分，確保隔離。

### 2.2 任務：全局 API 權限掛載 (Global Scope Mounting)
- **2.2.A: `blog_api.py` 現代化**: 將 1 月份的手寫 Role 檢查升級為 `CONTENT_PUBLISH/REJECT` Scope。
- **2.2.B: `mcp_api.py` 安全補強**: (待辦)
- **2.2.C: `admin_api.py` 升級**: (待辦)


### 2.3 任務：MCP 實體化與配置對齊 (MCP Functional Realization)
- **物理動作**: 讓 `mcp_api.py` 的 `/config` 讀取 `archon_settings` 或 `credential_service`。
- **目標**: 讓 3737 (Admin UI) 看到真實的 MCP 配置。

### 2.4 任務：PRP 4.6.28/29 遺留清點 (Legacy Cleanup)
- **物理動作**: 物理執行並核對 `rag_service.py` 的探針測試結果。

## 3. 物理驗證基準 (Verification Protocols)
1. **負面測試**: 使用 Employee 帳號呼叫 `GET /api/mcp/config`，預期應回傳 `403 Forbidden`。
2. **RLS 驗證**: 檢查 Supabase 稽核日誌，確認查詢帶有正確的 `auth.uid` 標籤。

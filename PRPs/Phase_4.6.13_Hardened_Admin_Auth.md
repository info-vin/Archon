# Phase 4.6.13 Hardened Admin Auth (FULLY VERIFIED 2026-03-18)

## 🟢 PHYSICAL SECURITY AUDIT: PASSED
- **Current State**: Admin UI (3737) uses a hardened M2M flow with `ADMIN_SECRET` validation.
- **Verification**: Confirmed via physical curl tests (403 on missing/invalid secret, 200 on valid).
- **Test Integrity**: Admin UI (3737) tests (135/135) remain passing in the new secure environment.

## 401 Unauthorized Remediation List
- [x] Refactor credentialsService.ts to use apiClient (Verified in Admin UI)
- [x] Audit and fix raw fetch calls in SettingsPage.tsx (Verified in Admin UI)
- [x] Audit and fix raw fetch calls in APIKeysSection.tsx (Verified in Admin UI)
- [x] **SECURE DEV-TOKEN**: Implement `ADMIN_SECRET` validation (DONE).

## Phase 4.6.12 Decomposition Audit (COMPLETED)
- **Projects API Hardening**: 🟢 **100% Physical Landing**. (Verified 2026-03-16)
- **End-User UI (5173) Decomposition**: 🟢 **100% Physical Landing**. (Verified 2026-03-17)

## Hardening Implementation (Physical Specs)
1. **Backend**: `auth_api.py` now enforces `X-Admin-Secret` header check.
2. **Frontend**: `AuthContext.tsx` automatically injects the secret from Vite environment.
3. **Infrastructure**: `.env` and `docker-compose.yml` synchronized with the new secret.
4. **2026-03-20 Config Hardening**: 實作 `TOKEN_PRICING_JSON` 動態解析，透過 JSON 格式將全系統財務模型與代碼物理脫鉤，增強營運配置的安全性與靈活性。
5. **2026-03-21 Config UI & DB Override (Phase 4.6.15)**: 
    *   在 Admin UI (5173) 的 `AdminSystemConfig.tsx` 實作前端編輯器。
    *   `config.py` 改為優先讀取 `archon_settings` 資料表，確保 UI 修改能物理生效。

## Verification Status
- **Backend Tests**: 🟢 541/541 Passed
- **Admin UI (3737) Tests**: 🟢 135/135 Passed (Executed via `npx vitest`)
- **End-User UI (5173) Tests**: 🟢 45/45 Passed
- **dev-token Accessibility**: 🟢 **HARDENED** (Confirmed 2026-03-18)

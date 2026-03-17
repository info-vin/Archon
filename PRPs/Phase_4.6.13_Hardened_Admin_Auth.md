# Phase 4.6.13 Hardened Admin Auth

## 401 Unauthorized Remediation List
- [x] Refactor credentialsService.ts to use apiClient (Verified in Admin UI)
- [x] Audit and fix raw fetch calls in SettingsPage.tsx (Verified in Admin UI)
- [x] Audit and fix raw fetch calls in APIKeysSection.tsx (Verified in Admin UI)
- [x] Ensure all 3737 requests include JWT headers (Verified via Vite Proxy + apiClient)

## Phase 4.6.12 Decomposition Audit (FULLY VERIFIED 2026-03-16)
- **Projects API Hardening**: 🟢 **100% Physical Landing**.
  - **Structure**: Created `api_routes/projects/` modular package.
  - **Core**: `core.py` handles projects/documents.
  - **Ops**: `ops.py` handles tasks/dispatching.
  - **Versioning**: `versioning.py` decoupled from monolith.
  - **Facade**: `projects_api.py` reduced to 38-line aggregator.
- **Error Handling (Deep Audit)**:
  - **404**: Explicitly handled in `core.py` for projects/documents.
  - **403**: Department Isolation and cross-dept assignment blocking implemented in `core.py`/`ops.py`.
  - **500/422**: Centralized `_err` handler verified.

## Phase 4.6.13.2: End-User UI (5173) Hardening (FULLY VERIFIED 2026-03-16)
- [x] **Infrastructure**: Created `apiClient.ts` with automatic JWT & RBAC (X-User-Role) injection.
- [x] **Error Mapping**: `apiClient.ts` verified to unpack backend error messages and statuses (401, 403, 404, 429).
- [x] **Persona Persistence**: Updated `useAuth.tsx` to persist `user_role` for Alice/Bob/Charlie/David protection.
- [x] **Import Alignment**: Synchronized 36 file imports to use extensionless `../services/api` paths.
- [x] **Modular Migration**: Total 86 raw fetch calls replaced.

## Verification Status
- **Backend Tests**: 🟢 541/541 Passed
- **Admin UI (3737) Tests**: 🟢 135/135 Passed
- **End-User UI (5173) Tests**: 🟢 45/45 Passed
- **Error Propagation**: 🟢 Verified (Backend -> Client -> Error Object)

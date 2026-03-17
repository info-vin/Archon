# Phase 4.6.13 Hardened Admin Auth

## 401 Unauthorized Remediation List
- [x] Refactor credentialsService.ts to use apiClient (Verified in Admin UI)
- [x] Audit and fix raw fetch calls in SettingsPage.tsx (Verified in Admin UI)
- [x] Audit and fix raw fetch calls in APIKeysSection.tsx (Verified in Admin UI)
- [x] Ensure all 3737 requests include JWT headers (Verified via Vite Proxy + apiClient)

## Phase 4.6.12 Decomposition Audit (FULLY VERIFIED 2026-03-16)
- **Projects API Hardening**: 🟢 **100% Physical Landing**.
  - **Facade**: `projects_api.py` reduced to 38-line aggregator.
- **Test Alignment**: 🟢 **Fixed 14/14 regressions** in backend tests.

## Phase 4.6.13.2: End-User UI (5173) Hardening (FULLY VERIFIED 2026-03-16)
- [x] **Infrastructure**: Created `apiClient.ts` with automatic JWT & RBAC (X-User-Role) injection.
- [x] **Persona Persistence**: Updated `useAuth.tsx` to persist `user_role` for Alice/Bob/Charlie/David protection.
- [x] **Import Alignment**: Synchronized 36 file imports to use extensionless `../services/api` paths.
- [x] **Modular Migration**: Total 86 raw fetch calls replaced.

## Phase 4.6.13.3: 5173 Monolith Decomposition (FULLY VERIFIED 2026-03-16)
- [x] **DashboardPage.tsx**: Reduced from 598 lines to 128 lines.
    - [x] Extracted `PriorityBadge` and `StatusBadge` to separate files.
    - [x] Extracted `ListView`, `TableView`, `KanbanView`, `GanttView` (Memoized).
    - [x] Extracted Dashboard Business Logic to `useDashboardLogic` Hook.
    - [x] Restored missing `attachment-badge` logic identified during testing.
- [ ] **ContentWorkbench.tsx (566 lines)**: Future decomposition target.

## Verification Status
- **Backend Tests**: 🟢 541/541 Passed
- **Admin UI (3737) Tests**: 🟢 135/135 Passed
- **End-User UI (5173) Tests**: 🟢 45/45 Passed (Zero regressions in Dashboard logic)
- **make dev-docker**: 🟢 Healthy

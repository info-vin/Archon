---
name: "Phase 4.5: System Institutionalization (系統制度化)"
description: |
  A strict refactoring phase to pay off the "Speed Debt" incurred during Phase 4.4.
  Focuses on normalizing UIs, converting scripts into proper APIs, and standardizing test suites.
  (這是一個嚴格的重構階段，旨在償還 Phase 4.4 為了追求速度所欠下的「技術債」。專注於 UI 正規化、將腳本轉化為正式 API，以及測試套件的標準化。)

---

## Goal (目標)

**Core Objective (核心目標)**: To move from "it works via script" to "it works via system architecture". (從「透過腳本運作」轉變為「透過系統架構運作」。)

**Deliverables (交付成果)**:
1.  **Unified Team UI (統一團隊介面)**: Replace the high-contrast "Dark Mode" Agent panel with standard "White Cards" that match human employees, distinguished only by badges/icons to reduce visual fatigue.
2.  **System Health API (系統健康 API)**: Migrate `scripts/probe_librarian.py` into `HealthService`, exposing a secure endpoint `GET /api/system/health/rag` for automated monitoring.
3.  **Standardized Test Suite (標準化測試)**: Relocate `python/test_crawler.py` to `python/tests/external/`, integrating it with the standard `pytest` runner.

**Success Definition (成功定義)**:
- **Visual**: The Team Management page looks consistent. No jarring dark blocks.
- **Automation**: `curl localhost:8181/api/system/health/rag` returns a JSON health report. `make probe` becomes a wrapper for this API.
- **QA**: `make test-external` runs the crawler test without manual arguments.

---

## All Needed Context (所有需要的上下文)

### Documentation & References (文件與參考資料)

```yaml
- file: enduser-ui-fe/src/pages/TeamManagementPage.tsx
  why: Current UI implementation containing the "Indigo Panel" to be removed.
- file: scripts/probe_librarian.py
  why: Source logic for the RAG probe, to be ported to backend Service.
- file: python/src/server/services/health_service.py
  why: Destination service for the probe logic.
- file: python/test_crawler.py
  why: The orphan script to be adopted into the pytest family.
```

### Risk Analysis (風險分析 - "Don't Break B")

| Change | Potential Risk (潛在風險) | Mitigation Strategy (緩解策略) |
| :--- | :--- | :--- |
| **UI Refactor** | Removing the panel might hide "AI Quota" info. | Move Quota usage to the Agent's card or a subtle Header Summary. |
| **Probe Migration**| The script does actual DB writes (Seeding). API calls might pollute DB if run frequently. | Add `dry_run` flag or ensure the API uses a `ROLLBACK` transaction if possible, or explicitly marks data as `is_test=True`. |
| **Test Move** | `test_crawler.py` uses `httpx`. `pytest` env might miss dependencies? | Confirmed `pyproject.toml` has `httpx`. Will mark test as `@pytest.mark.external` to avoid blocking CI. |

---

## Implementation Blueprint (實作藍圖)

### Step 1: The UI Normalization (Frontend)
*Target: `enduser-ui-fe/src/pages/TeamManagementPage.tsx`*

1.  **Remove**: Delete the `bg-indigo-900` section (Lines 158-189).
2.  **Unify**: Render Agents inside the main `team.map` loop (or a secondary mapped list in the same grid).
3.  **Component**: Create a visual mapping for Agents:
    *   **Avatar**: Use a Robot Emoji 🤖 or specific Icon based on role (🛠️, 📈).
    *   **Badge**: Display "AI Agent" instead of "Sales/Marketing".
    *   **Stats**: Display "Quota: 128/200" in the slot where Human Email usually goes.

### Step 2: The Service Migration (Backend)
*Target: `python/src/server/services/health_service.py` & `api_routes/system_api.py`*

1.  **Refactor**: Create method `check_rag_integrity()` in `HealthService`.
    *   Copy logic from `scripts/probe_librarian.py`.
    *   **Crucial**: Remove `sys.path` hacks. Use proper dependency injection for `RAGService` and `LibrarianService`.
    *   **Improvement**: Return a structured `HealthCheckResult` Pydantic model instead of printing to stdout.
2.  **Endpoint**: Add `GET /api/system/health/rag`.
    *   Security: Require `SYSTEM_ADMIN` role (or `MANAGER`).
3.  **Clean Up**: Delete `scripts/probe_librarian.py` after verification.

### Step 3: The Test Standardization (QA)
*Target: `python/tests/external/test_104_reliability.py`*

1.  **Relocate**: Move logic from `python/test_crawler.py`.
2.  **Pytest-ify**:
    *   Convert `CrawlerTestRunner` class to a standard test function `test_104_crawler_reliability()`.
    *   Use `pytest.mark.external` decorator.
    *   Replace `print` with `logging` or `pytest` assertions.
3.  **Config**: Update `pytest.ini` to register the `external` marker.

---

## Q&A (針對您的疑慮)

### Q1: Why was the Agent panel dark?
**Analysis**: Originally designed to visually separate "Tools" from "People".
**Correction**: It violates the "Unified Workforce" philosophy of Phase 5. Agents should be treated as team members. We will fix this by using consistent card designs.

### Q2: Is `make probe` a script?
**Analysis**: Currently yes (`python scripts/probe_librarian.py`).
**Correction**: This is bad practice for a production system. By moving it to `HealthService`, `Clockwork` can import the class directly, and external monitors can call the API. `make probe` will remain but will be updated to `curl` the API instead.

### Q3: Where do tests go?
**Analysis**: `test_crawler.py` in root is messy.
**Correction**: All tests must live in `tests/`. Since this tests an external 3rd party service (104), it belongs in `tests/external/` to differentiate it from Unit (Code logic) and Integration (DB logic) tests.

---

## Validation Steps (驗收步驟)

1.  **UI**: Open `/team`. Verify Agents appear as white cards. No eye-straining dark blocks.
2.  **API**: Run `curl -X GET http://localhost:8181/api/system/health/rag -H "Authorization: Bearer <ADMIN_TOKEN>"`. Expect `200 OK` with JSON report.
3.  **Test**: Run `make test-external` (alias for `pytest -m external`). Verify 104 crawler runs.

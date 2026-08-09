## 2026-08-07 - Python Type Refactoring without breaking dependent unit tests
**Learning:** When tests in `python/tests` fail due to missing dependencies during verification steps, verify if all declared dependencies have been synchronized to the testing environment. Missing packages like `httpx` and `fastapi` caused test execution to fail initially.
**Action:** Use `uv sync --all-groups` explicitly before running `pytest` to ensure all required testing dependencies exist before considering a test suite broken by a refactoring change.
## 2026-08-09 - Scoping Test Execution to Bypass Unrelated Failures
**Learning:** When running Python tests in a large codebase, if executing the entire suite (e.g., `pytest tests/`) fails due to unrelated environment constraints or external mock requirements (like missing `GOOGLE_API_KEY` for agents), it can block verification.
**Action:** Scope the test execution directly to the relevant directories (e.g., `uv run pytest tests/unit/ tests/server/services/`) to verify business logic changes and isolate them from integration-heavy or external-dependent failures.

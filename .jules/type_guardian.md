## 2026-08-07 - Python Type Refactoring without breaking dependent unit tests
**Learning:** When tests in `python/tests` fail due to missing dependencies during verification steps, verify if all declared dependencies have been synchronized to the testing environment. Missing packages like `httpx` and `fastapi` caused test execution to fail initially.
**Action:** Use `uv sync --all-groups` explicitly before running `pytest` to ensure all required testing dependencies exist before considering a test suite broken by a refactoring change.

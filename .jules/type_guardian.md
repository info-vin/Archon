## 2026-08-07 - Python Type Refactoring without breaking dependent unit tests
**Learning:** When tests in `python/tests` fail due to missing dependencies during verification steps, verify if all declared dependencies have been synchronized to the testing environment. Missing packages like `httpx` and `fastapi` caused test execution to fail initially.
**Action:** Use `uv sync --all-groups` explicitly before running `pytest` to ensure all required testing dependencies exist before considering a test suite broken by a refactoring change.
## 2026-08-09 - Scoping Test Execution to Bypass Unrelated Failures
**Learning:** When running Python tests in a large codebase, if executing the entire suite (e.g., `pytest tests/`) fails due to unrelated environment constraints or external mock requirements (like missing `GOOGLE_API_KEY` for agents), it can block verification.
**Action:** Scope the test execution directly to the relevant directories (e.g., `uv run pytest tests/unit/ tests/server/services/`) to verify business logic changes and isolate them from integration-heavy or external-dependent failures.
## 2025-03-09 - Optional Dependencies in Service Layers
**Learning:** External dependencies like `curl_cffi` may need to be imported at the module level when used for typing (e.g., `Session`) instead of using untyped `Any`, provided they are part of the core environment (which we verify via standard tests).
**Action:** When replacing `Any` types with objects from external clients, import the concrete class from the client module.
## 2024-08-14 - Use TypedDict for backward compatibility
**Learning:** When refactoring existing services to return structured DTOs instead of `dict[str, Any]`, using `@dataclass` or `BaseModel` can break downstream callers and tests that use dictionary subscripting (e.g., `result["key"]`), resulting in `TypeError`.
**Action:** Use `TypedDict` for DTOs in incremental refactors where you cannot guarantee all call sites are simultaneously updated, as it provides static type safety while remaining 100% backward compatible at runtime.
## 2025-03-01 - ParamSpec kwargs restriction
**Learning:** `ParamSpec.kwargs` can only be used in conjunction with `ParamSpec.args` and must be bound to a generic context (such as taking a `Callable[P, ...]`). Using it standalone on a standard method will cause static type checkers to fail. The correct annotation for untyped, variable keyword arguments in standard methods is `**kwargs: Any` or to replace them with explicit keyword arguments.
**Action:** Always replace `**kwargs` with explicit arguments when possible to favor explicit over implicit. Do not use `ParamSpec.kwargs` outside of its intended generic context.
## 2025-03-09 - Type Hinting Optional Return Types with TypeVar
**Learning:** When a method's return type depends on an unbound generic TypeVar `T` (e.g., `default: T = None`), strict type checkers might flag `None` as incompatible if `T` itself does not encompass `None`.
**Action:** When using `TypeVar` for default arguments that can be `None`, explicitly type the return signature to include the `TypeVar` along with the other possible return types (e.g., `T | str | dict[str, Any] | None`).

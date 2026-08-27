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
## 2026-08-23 - Type Hinting Missing Return annotations and kwargs
**Learning:** Found multiple methods in service files (`threading_service.py`, `background_task_manager.py`, `source_management_service.py`) that were missing either explicit return types (like `-> None:` or `-> AsyncGenerator[None, None]:`) or argument type annotations specifically for `*args` and `**kwargs` (like `*args: Any` or `**kwargs: Any`).
**Action:** Always ensure explicitly specifying `*args: Any` and `**kwargs: Any` if their types are not strictly defined, rather than leaving them untyped. Ensure all methods, especially setup or cleanup methods, have explicit return types even if it is just `-> None:`.
## 2024-05-18 - Type Hinting supabase_client
**Learning:** When type hinting `supabase_client` initialization parameters in the Python backend (e.g., in `server/services/` or `server/repositories/`), import `Client` from the `supabase` package and explicitly annotate it as `Client | None = None` instead of leaving it untyped or using `typing.Any`.
**Action:** Use `from supabase import Client` and `Client | None = None` for `supabase_client` arguments in `__init__` methods.
## 2024-05-18 - Safe Refactoring of Legacy Tuple Types
**Learning:** When refactoring legacy APIs that returned `tuple[bool, dict[str, Any]]` to use stricter Types/DTOs, adding `dict[str, Any]` to the return type union (e.g. `tuple[bool, ProjectResultDTO | dict[str, Any]]`) undermines static analysis entirely, because MyPy will still allow arbitrary key access under the assumption it might be a dict. `cast()` handles the boundary, but the signature must be strict to protect callers.
**Action:** When migrating legacy dict returns to DTOs using `TypedDict`, do not union the DTO with `dict[str, Any]` in the function signature. Instead, union it with the error type (like `str` for error messages) and rely on `cast(DTO, result)` to enforce the contract at the repository boundary, ensuring all upstream consumers benefit from the strict type.
## 2024-05-24 - LLM Proxy Wrappers and Any Typing
**Learning:** Adding type annotations to dynamically proxied wrapper methods in Python (like decorators and external SDK proxies like `original_client: Any` or `_execute_on_hf() -> Any`) without using `Any` or `# type: ignore` is extremely complex due to unknown kwargs structures from underlying SDKs, which would require massive architectural refactoring. However, per TypeGuardian guidelines, we should strive to avoid `Any` wherever possible.
**Action:** Avoid blindly annotating proxy/wrapper `args` and `kwargs` as `Any` or using `type: ignore` if possible, and document instances where it is temporarily acceptable but not ideal for `TypeGuardian` rules.

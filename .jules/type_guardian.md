# TypeGuardian Guidelines (Consolidated)

## 1. Prefer TypedDict DTOs Over dict[str, Any]
**Learning:** Replacing untyped `dict` with `dict[str, Any]` cheats static type checking, while converting legacy dict returns to `@dataclass` or `BaseModel` can break downstream callers using `result["key"]` subscripting.
**Action:** Define structured `TypedDict` DTOs (using `NotRequired` for optional/partial fields) to enforce strict static contracts while maintaining 100% runtime dictionary compatibility, and keep wrapper/delegation method signatures in sync with strategy DTOs.

## 2. Strict Return Signatures Without dict[str, Any] Unions
**Learning:** Unioning a `TypedDict` DTO with `dict[str, Any]` in a return signature (e.g., `tuple[bool, ResultDTO | dict[str, Any]]`) undermines MyPy checks for all callers.
**Action:** Union the DTO only with explicit error types (e.g., `tuple[bool, ResultDTO | str]`) and use `cast(ResultDTO, result)` at the repository boundary.

## 3. Dependency Injection and Circular Import Prevention
**Learning:** Subclasses of `BaseRepository` should support explicit client injection for testing, and importing cross-module services at runtime for type hints can trigger circular `ImportError` crashes.
**Action:** Annotate repository/service constructors with `supabase_client: Client | None = None`, and guard cross-module type imports behind `if TYPE_CHECKING:` using modern `X | None` union syntax (Ruff `UP045`).

## 4. Preserve SSOT Audit Markers (# 合法) and Verify with Full Sync
**Learning:** Removing `# 合法` comments on exempted literals causes `make phase-audit` (Step 8 SSOT check) to fail, and running `pytest` without syncing all dependency groups causes false import errors.
**Action:** Never strip existing `# 合法` SSOT markers during type refactors, and always run `uv sync --all-groups` followed by `mypy src --ignore-missing-imports` to verify zero regressions across all source files.

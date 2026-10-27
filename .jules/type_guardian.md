# TypeGuardian Guidelines (Consolidated)

## 1. Ban Cosmetic `cast()` Lying — Match True Runtime Shapes (IRON LAW)
**Learning:** `TypedDict` performs zero runtime validation. Defining a strict `TypedDict` (e.g., `api_key: str` or invented keys in `PitchResultDict`) when the function can actually return `None` or different keys at runtime, or wrapping an unverified `execute_query` dict with `cast(SomeDTO, result)`, creates false type safety that hides real runtime bugs from MyPy.
**Action:**
- Never use `cast(DTO, ...)` to paper over a mismatch between what `BaseRepository.execute_query()` or a handler actually returns and what callers expect.
- If a variable can be `None`, `dict`, or `str` at runtime, the `TypedDict` field MUST reflect the true union (`str | None`) and runtime type-narrowing (`isinstance(...)`) MUST be used instead of `cast()`.

## 2. Substance Over Pure Annotation Churn & Zero JSONB Ossification
**Learning:** PRs that only add `TypedDict` definitions and `cast()` calls without improving runtime safety create structural rigidity without business value, and forcing dynamic JSONB dicts (`docs`, `metadata`, `content`) into rigid DTOs breaks flexibility.
**Action:** Pair static `TypedDict` DTOs with genuine runtime boundary guards (e.g., distinguishing encrypted metadata dicts `EncryptedCredentialDict` from plaintext `str` values in credential caches, or validating list/dict structures before indexing), and leave free-form JSONB payloads as `dict[str, Any]`.

## 3. Full-Chain Signature & Caller Alignment (Rule 13)
**Learning:** Narrowing a service return signature or changing dict keys without checking both the deep handler/repository producer and all callers/test mocks breaks downstream unpacking or leaves DTOs out of sync with reality.
**Action:** Before defining or changing any DTO or return signature, inspect the deepest handler implementation and `grep` all callers across `src/` and `tests/` to verify 100% key and type alignment.

## 4. Dependency Injection, Circular Imports & SSOT Markers (# 合法)
**Learning:** Importing cross-module services at runtime for type hints causes circular `ImportError`, and stripping `# 合法` comments breaks `make phase-audit` Step 8.
**Action:** Annotate repository/service constructors with `supabase_client: Client | None = None`, guard cross-module type imports behind `if TYPE_CHECKING:`, use `X | None` syntax, preserve all `# 合法` markers, and verify with `mypy src` and `pytest`.

## 2025-05-18 - Async Service Methods Blocking Event Loop via Synchronous DB Execution
**Learning:** In service classes inheriting from `BaseRepository`, invoking synchronous `self.execute_query(...)` inside `async def` methods causes database queries to run synchronously on the main thread, blocking the event loop. Furthermore, blind `res["data"][0]` access after `execute_query` risks `TypeError` or `IndexError` when `res.get("data")` is not a non-empty list.
**Action:** Always use `await self.execute_query_async(...)` inside `async def` service methods, and inspect `isinstance(res.get("data"), list)` and non-emptiness before indexing list elements.

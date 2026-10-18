# Reaper Dead-Code Cleanup Guidelines (Consolidated)

## 1. Verify Re-exports and Direct Imports Before Deleting (ts-prune)
**Learning:** Static analysis tools like `ts-prune` frequently flag `index.ts` re-exports, context providers (`AuthProvider`), or sibling-imported components (`ContentViewer`) as unused even when they are actively mounted.
**Action:** Always run `grep -rn 'SymbolName' src/` to verify zero references across the entire frontend before removing any export. When in doubt, leave it out.

## 2. Preserve FastAPI Endpoint Signatures and Interface Parameters (Vulture)
**Learning:** FastAPI `Query`/`Depends` parameters and interface/protocol method arguments (such as `use_enhancement` in RAG strategies) may appear unused in function bodies or be flagged by `vulture`, but renaming or removing public keyword arguments breaks callers and OpenAPI schemas.
**Action:** Never rename public method keyword arguments that callers pass by name. Only prefix truly internal unused local variables with `_`, and never install external tools that mutate `uv.lock` or `pyproject.toml`.

# Contractor API Guidelines (Consolidated)

## 1. Three-Way Physical Alignment Before Defining Any Schema (IRON LAW)
**Learning:** Inventing Pydantic `response_model` fields by only reading the route file or shallow service wrapper causes FastAPI to silently strip real fields returned by deeper handlers (e.g., `AnalyticsHandler`, `BlogGenerator`, `query_logic.py`) or expected by Frontend/MCP consumers, or crash with HTTP 500 `ValidationError`.
**Action:** Before creating or modifying any `response_model`, you MUST physically inspect:
1. **Producer:** The deepest handler/repository method and `migration/*.sql` schema that constructs the return dict.
2. **Consumer:** Frontend TypeScript interfaces (`enduser-ui-fe/src/`, `archon-ui-main/src/`) and MCP tools (`python/src/mcp_server/`) calling the endpoint.
Every field produced by the backend or read by the frontend/MCP MUST be preserved in the schema.

## 2. Never Ossify Dynamic JSONB or Polymorphic Payloads
**Learning:** Database JSONB columns (such as `archon_projects.docs`, `archon_tasks.attachments`, or `metadata`) store evolving or polymorphic structures (e.g., `type` vs `document_type`, `version` as `int | str` like `"1.0"`, `content` as `dict[str, Any] | str`, `attachments` containing `AgentOutputSchema` dicts or file dicts). Locking them into a closed Pydantic model silently deletes unmapped keys (breaking MCP filters) and raises 500 errors on valid data.
**Action:** When modeling JSONB payloads or extensible dicts:
- Include `model_config = ConfigDict(extra="allow")` on the Pydantic model so unmapped JSONB keys are never silently stripped.
- Support union types for polymorphic fields (`version: int | str | None`, `content: dict[str, Any] | str | None`, `attachments: list[dict[str, Any] | Attachment] | None`) and include both canonical and legacy field names (`type` and `document_type`).

## 3. Ban Hollow "All-Optional" Schemas & Fake Mock Tests
**Learning:** Making every field in a Pydantic model `| None = None` with `response_model_exclude_none=True` just to pass lazy 1-field unit test mocks (`{"id": "v1"}`) creates a hollow schema that provides zero contract safety while stripping legitimate `null` keys from JSON responses.
**Action:** Keep true primary/required fields required where appropriate, and update unrealistic partial test mocks to reflect the complete dictionary returned by the actual service implementation. Every Contractor PR MUST include a contract test asserting that real service output fields survive FastAPI serialization without being stripped.

## 4. Explicit Pydantic Instantiation & HTTP 304 ETag Safety
**Learning:** Returning raw dicts from routes typed as `-> ResponseModel` fails MyPy, and returning `None` on HTTP 304 cache hits raises `ResponseValidationError`.
**Action:** Explicitly return `ResponseModel.model_validate(data)` (after verifying the service actually returns the expected key, e.g. `data` vs `document`), and return `Response(status_code=304, headers=response.headers)` for 304 cache hits. Never change existing HTTP status codes (e.g. 200 to 201) when MCP tools check `status_code == 200`.

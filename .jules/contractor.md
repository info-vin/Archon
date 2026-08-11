
## 2026-07-23 - Hardened log_api /record-gemini-log
**Learning:** Returning dictionaries with potential error keys in FastAPI endpoints that signify successful completion (status 201) can cause schema mismatches if the Pydantic schema strictly expects nested data (like `{"log": {}}`). Handled by ensuring `log` and `error` keys are typed as Optional, allowing both successful dicts and error dicts to pass serialization without triggering an Internal Server Error.
**Action:** Always carefully trace the raw return dict of the underlying service (e.g. `log_service.create_log_entry`) to include all possible dynamic fields (like failure structures) in the Pydantic ResponseModel when adding strict types.
## 2026-08-01 - Omission of Field(description=...) in simple Pydantic models\n**Learning:** When creating simple Pydantic Response schemas that map directly to standard JSON payloads without complex structures, occasionally omitting `Field(description=...)` doesn't break functionality, but strictly adhering to Contractor's preferred pattern by adding it improves API documentation quality. Code reviewers might catch this omission.\n**Action:** Ensure all Pydantic model attributes for FastAPI endpoints are annotated with `Field(description=...)` moving forward to satisfy OpenAPI documentation standards and avoid nitpicks during review.

## 2026-08-05 - Missing explicit instantiation of Pydantic models in FastAPI returns
**Learning:** When adding a strict return type hint (`-> list[LeadResponse]`) to a FastAPI route that previously returned a list of dictionaries, returning the raw list of dictionaries causes static type checkers (`mypy`, `pyright`, or strictly typed linting rules) to fail with an incompatible type error, even though FastAPI itself will correctly coerce dictionaries to Pydantic models at runtime via `response_model`.
**Action:** When annotating a FastAPI route handler with a specific Pydantic return type, you must explicitly instantiate the model(s) before returning (e.g., `return [MyModel(**item) for item in items]`) to ensure strict Python static type checking passes.

## 2025-05-18 - Untyped GET /health endpoints
**Learning:** Found several `GET /health` endpoints returning untyped dictionaries (e.g. `{"status": "healthy"}`) directly instead of using a Pydantic `response_model` schema. While simple, they fail the strict OpenAPI contract compliance required for Contractor.
**Action:** Always create a quick `BaseModel` for `/health` responses and use `response_model=HealthResponse` in the `@router.get` decorator to ensure 100% type safety on all endpoints, no matter how trivial.
## 2024-08-08 - Added RBACRoleResponse to Admin API
**Learning:** Returning a raw dict when the route is typed with a Pydantic `response_model` will cause type-checkers (like ruff/mypy) to complain about incompatible return value types in the handler if we declare `-> RBACRoleResponse`.
**Action:** Always instantiate the exact Pydantic model (`return RBACRoleResponse(**data)`) inside the route handler when explicit type annotations are used.
## 2025-02-23 - Hardened get_commander_trends API endpoint
**Learning:** Returning a raw list of dictionaries mapped from `stats_service` leaves the API susceptible to schema drift and lacks OpenAPI integration.
**Action:** Always instantiate Pydantic models (e.g., `[CommanderTrend(**r) for r in results]`) within the route handler to ensure strict serialization and drop unexpected extra fields before they hit the client, even if FastAPI might cast dicts at runtime.
## 2024-08-10 - Preserving JSON Payload Structure with Pydantic Alias
**Learning:** When refactoring existing API routes to use strict Pydantic schemas, Python reserved keywords (like `from`) used as JSON keys will cause syntax errors if defined directly as class attributes.
**Action:** Use Pydantic's `Field(alias="from")` combined with a safe Python attribute name (e.g., `from_node`) to strictly type the payload while perfectly preserving the existing JSON serialization structure, ensuring frontend clients do not break.

# Contractor API Guidelines (Consolidated)

## 1. Explicit Pydantic Response Models and Instantiation
**Learning:** Returning raw dictionaries from FastAPI routes annotated with a Pydantic return type (`-> ResponseModel`) works at runtime via coercion but fails MyPy static type checking.
**Action:** Always declare `response_model=ResponseModel` on the route decorator and explicitly return `ResponseModel(**data)` or `ResponseModel.model_validate(data)` while preserving the underlying service call and tuple-unpacking logic.

## 2. HTTP 304 Not Modified Handling with response_model
**Learning:** When adding `response_model` to FastAPI routes that support ETag caching, returning `None` on HTTP 304 cache hits causes FastAPI to validate `None` against the Pydantic schema and raise `ResponseValidationError`.
**Action:** Always return an explicit `Response(status_code=304, headers=response.headers)` instance for 304 cache hits.

## 3. Align Route Schemas with Service DTOs
**Learning:** Defining loose `list[dict[str, Any]]` fields in Pydantic route schemas when the service returns strict `TypedDict` DTOs causes MyPy invariance errors (`Incompatible types in assignment`).
**Action:** Import and reference the exact `TypedDict` DTOs from the service layer inside Pydantic response models, or cast at the boundary when needed.

## 2025-05-18 - Response Model Validation on HTTP 304 Returns
**Learning:** When adding a Pydantic `response_model` to FastAPI routes that handle ETag caching, returning `None` for HTTP 304 Not Modified causes FastAPI to attempt validating `None` against the `response_model`, triggering a `ResponseValidationError`.
**Action:** Always return an explicit `Response(status_code=304, headers=response.headers)` object when handling 304 cache hits in routes with `response_model` specified.

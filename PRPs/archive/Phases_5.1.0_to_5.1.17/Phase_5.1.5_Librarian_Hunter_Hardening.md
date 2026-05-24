# Implementation Plan - Librarian Hunter Mode Hardening

Stabilize the Librarian Hunter Mode RAG pipeline by resolving the `INVALID_ARGUMENT (thought_signature)` error and aligning environments across `archon-server` and `archon-agents`.

## User Review Required

> [!IMPORTANT]
> **Environment Mismatch Detected**: `archon-agents` is running `pydantic-ai 1.44.0` while `archon-server` is running `0.0.55`. The proposed changes will make the code compatible with both, but a full rebuild of `archon-server` is recommended for physical parity.

> [!WARNING]
> **Provider Migration**: We are moving from the legacy `GoogleGLAProvider` to the modern `GoogleProvider` for environments running PydanticAI v1.x to support Gemini 3.1 reasoning features.

## Proposed Changes

### 🛡️ Core Infrastructure

#### [MODIFY] [workflow_engine.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/workflow_engine.py)
- **Version Detection**: Refine `PAI_V1` detection and usage.
- **Provider Factory**: Update `_run_agent_with_retry` to dynamically select `GoogleProvider` (v1) or `GoogleGLAProvider` (v0).
- **Output Compatibility**: Ensure `_get_output` correctly handles the transition from `.data` to `.output`.

#### [MODIFY] [resilience.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/utils/resilience.py)
- **Model Alignment**: Update fallback logic to use `gemini-3.1-flash-lite` instead of `-preview` versions.

### 🧪 Verification & Testing

#### [MODIFY] [verify_librarian_hunter.py](file:///Users/vincenta/GoogleKwok022/Archon/scripts/verify_librarian_hunter.py)
- **Container Target**: Update internal documentation to emphasize running tests inside `archon-agents` for the most accurate results.

## Verification Plan

### Automated Tests
1. **Containerized Validation**:
   - Run `docker exec archon-agents python src/agents/test_ai_version.py` to verify basic connectivity.
   - Run `docker exec archon-server python scripts/verify_librarian_hunter.py` to verify cross-version compatibility.
2. **Librarian RAG Test**:
   - Execute the hunter mode verification to confirm successful crawling and citation generation.

### Manual Verification
- Verify that the `thought_signature` error no longer appears in the logs during agent execution.
- Confirm that API Key rotation (GEMINI -> GOOGLE) works correctly when simulated.

name: "Phase 5.5.7 - Nexus Metrics Consolidation & Meta-Twin Self-Healing Loop"
description: |
  Consolidate the overlapping and redundant metrics fetched by Charlie's Manager Nexus dashboard into a single, type-safe API driven by PydanticAI. Create an internal "Meta-Twin" monitoring system that treats active AI Agents as entities, tracking their status (token usage, latency, exceptions) and applying dynamic self-healing modifications.

---

## Goal

**Feature Goal**: Consolidate 15 separate metrics endpoints into a single PydanticAI-powered endpoint `/api/nexus/consolidated` that aggregates overview metrics, resource burn, pending approvals, and active warnings. Additionally, implement an event-driven background monitoring loop that tracks agent telemetry and performs automated healing (model swap, throttling) when issues are detected.

**Deliverable**:
- `NexusOracleAgent` in `nexus_oracle_agent.py` to compile and summarize metrics with structured outputs.
- central GET API route `/internal/nexus/consolidated` in `internal_api.py`.
- `meta_twin_service.py` to run background telemetry audits and execute actuators (fallback models, throttling limits).
- Refactored `useManagerNexusStats.ts` on frontend to use the consolidated API.

**Success Definition**:
- Admin panel fetches single API instead of 15 HTTP requests.
- Consolidated metrics structure successfully separates short-term (24h) and long-term (7d/30d) budget/token cycles.
- Background loops run telemetry audits and trigger actuators under simulated rate-limit or deadlock errors.
- Both manual and automated validation scripts pass without regressions.

## Why

- Charlie's dashboard fetches 15 redundant URLs, causing front-end latency, unnecessary database connections, and cognitive overload.
- Integrating PydanticAI allows for robust Structured Outputs (`result_type`) and asynchronous gathering (Map-Reduce).
- Auto-healing loops protect the workspace from infinite agent loops and budget leaks, ensuring production-grade resilience.

## What

### Success Criteria

- [x] Centralized `NexusOracleAgent` created and running successfully.
- [x] API endpoint `/internal/nexus/consolidated` registered and integrated with the agent.
- [x] `meta_twin_service.py` implemented with Clockwork cron orchestration.
- [x] Front-end `useManagerNexusStats.ts` refactored to fetch only the consolidated endpoint.
- [x] High-fidelity E2E Playwright test simulating Charlie's dashboard loading.
- [x] `make twin-scout` metric alignment scanner verification passes.

## Implementation Blueprint

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE python/src/agents/nexus_oracle_agent.py
  - IMPLEMENT: Define ConsolidatedNexusState Pydantic model. Gather metrics in parallel via Map-Reduce logic.

Task 2: MODIFY python/src/server/api_routes/internal_api.py
  - IMPLEMENT: Register /internal/nexus/consolidated endpoint and bind to NexusOracleAgent.

Task 3: CREATE python/src/server/services/system/meta_twin_service.py
  - IMPLEMENT: Define AgentTelemetry schemas, Clockwork cron triggers, and fallback/throttling actuators.

Task 4: MODIFY archon-ui-main/src/features/manager/hooks/useManagerNexusStats.ts (or enduser-ui-fe)
  - IMPLEMENT: Replace Promise.allSettled block with api.getConsolidatedNexusState().

Task 5: CREATE python/tests/server/test_nexus_oracle.py & E2E Validation
  - IMPLEMENT: Unit tests for oracle outputs. Playwright test for dashboard. Twin Scout metric alignment check.
```

## Validation Loop

### Level 1: Backend & Frontend Tests
```bash
cd python && uv run pytest tests/server/test_nexus_oracle.py
cd archon-ui-main && pnpm run lint && pnpm run test
```

### Level 2: Twin Scout Verification
```bash
make twin-scout T=consolidated_nexus_audit
```

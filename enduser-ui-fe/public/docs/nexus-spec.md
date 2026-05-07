# Nexus Metrics Specification (Phase 4.6.3)

The Nexus Command serves as the strategic orchestrator's central dashboard.

## Core Metrics

### System Integrity Analysis
* **Goal**: Ensure the RAG Vector Database is healthy and nodes are properly aligned.
* **Calculation**: Driven by vector dimensionality parity and `knowledge_roi` analytics.

### Resource & Synergy Audit
* **Goal**: Monitor the Human-Bot Collaboration window and Token budget burn-up.
* **Calculation**: Driven by `collabSynergy` and `aiStats`.

### Operational Load
* **Goal**: Monitor the decision queue for pending approvals across Marketing (Bob) and Engineering (DevBot).
* **Calculation**: Driven by `approvals` (blogs, leads) and `codeProposals`.

### Sentinel Risks
* **Goal**: Identify exceptions such as stale leads or failing tasks.
* **Calculation**: Driven by `alerts` from the `BusinessSentinel` background task.

*Documentation updated as of Phase 4.6.3 (2026-05-07).*
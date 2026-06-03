# Nexus Metrics Specification (Phase 5.5.7)

The Nexus Command serves as the strategic orchestrator's central dashboard.

## Core Metrics Definition & Calculation

### 1. System Integrity Analysis (`integrity`)
* **Goal**: Ensure the RAG Vector Database is healthy and all system nodes are aligned.
* **Calculation & Source**: Checks RAG vector dimension parity and search functionality. Uses health checks from `HealthService` to generate a composite score.
* **Colors**: Green (good/healthy) or Red (bad/critical failure).

### 2. Resource & Synergy Audit (`resources`)
* **Goal**: Track daily token usage costs against monthly budget limits.
* **Calculation & Source**: Accumulates OpenAI/Gemini token costs over the last 24 hours.
* **Colors**: Neutral (standard operation).

### 3. Operational Load (`op_load`)
* **Goal**: Monitor the decision queue for pending approvals across Marketing (Bob) and Engineering (DevBot).
* **Calculation & Source**: Total pending items in approvals (such as review blog posts) plus pending code change proposals.
* **Colors**: Green (no pending actions) or Yellow/Warning (items awaiting review).

### 4. Sentinel Risks (`sent_risks`)
* **Goal**: Exceptions radar tracking stale leads, tasks blockages, or background process anomalies.
* **Calculation & Source**: Active alerts logged by the `BusinessSentinel` background patrol daemon.
* **Colors**: Green (no alerts/all systems nominal) or Red (active warnings/errors).

### 5. Active Force (`active_force`)
* **Goal**: Status and availability roster for agents and team members.
* **Calculation & Source**: Online count of registered agents and active members.
* **Colors**: Green (active availability).

### 6. Ethics & Prompt Audit (`ethics`)
* **Goal**: Centralized safety compliance and prompt versioning alignment.
* **Calculation & Source**: Counts safety flags, content violations, and prompt change requests waiting for approval.
* **Colors**: Green (system nominal) or Red (pending safety flags or version updates).

### 7. Collab Synergy (`collab`)
* **Goal**: Tracks cross-department communication bridges and word count momentum.
* **Calculation & Source**: Measures momentum percentage of shared team task completions over 7 days.
* **Colors**: Green (positive momentum) or Yellow/Warning (declining or stagnant collaboration).

### 8. Intelligence ROI & Graph (`graph`)
* **Goal**: Measures the efficiency and overall conversion ROI of the knowledge base.
* **Calculation & Source**: Percentage of overall conversion based on seeded documents vs total nodes tracked.
* **Colors**: Green (high conversion/ROI), Yellow/Warning (medium), or Red (poor conversion).

### 9. SLA Reliability (`velocity`)
* **Goal**: Strategic discipline index monitoring milestone completion pacing.
* **Calculation & Source**: Tracks historical 6-month SLA achievement percentages.
* **Colors**: Green (SLA >= 95%) or Yellow/Warning (SLA < 95%).

### 10. System Prompts (`prompts`)
* **Goal**: Direct view and adjustments for AI agents' instruction profiles.
* **Calculation & Source**: Direct query of prompts configuration settings.
* **Colors**: Neutral.

*Documentation updated as of Phase 5.5.7 (2026-06-03).*
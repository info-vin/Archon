name: "Phase 5.5.6 - Giant Components Modularization & Tech Debt"
description: |
  Refactor and modularize giant React components and hooks to improve maintainability, reduce churn, and prevent merge conflicts.

---

## Goal

**Feature Goal**: Modularize `ArchonChatPanel.tsx` (461 lines) and `useKnowledgeMutations.ts` (517 lines) into smaller, single-responsibility components and hooks.

**Deliverable**: 
- A refactored `ArchonChatPanel.tsx` that acts as a container, delegating UI to sub-components and logic to custom hooks.
- A set of domain-specific mutation hooks (`useCrawlMutations`, `useUploadMutations`, `useItemMutations`) exported via `useKnowledgeMutations.ts` to maintain backward compatibility.

**Success Definition**: 
- Both original files are significantly reduced in size.
- Zero functionality loss (UI behavior, optimistic updates, and error handling remain identical).
- All frontend tests, linters, and builds pass.

## Why

- `ArchonChatPanel.tsx` has high churn (modified 8 times recently) and mixes UI presentation with complex WebSockets/Session logic. It's a "God Component".
- `useKnowledgeMutations.ts` is overly complex due to optimistic update rollbacks. Breaking it down will prevent bugs when adding future features.
- Modularization reduces merge conflicts and improves developer experience (DX).

## What

### Success Criteria

- [ ] `ArchonChatPanel.tsx` logic extracted into `useChatSession.ts` and `usePanelResize.ts`.
- [ ] `ArchonChatPanel.tsx` UI extracted into `ChatHeader.tsx`, `ChatMessageList.tsx`, and `ChatInput.tsx`.
- [ ] `useKnowledgeMutations.ts` split into `useCrawlMutations.ts`, `useUploadMutations.ts`, and `useItemMutations.ts`.
- [ ] Original `useKnowledgeMutations.ts` acts as a Facade exporting the split hooks.
- [ ] Frontend builds successfully.
- [ ] Frontend linter passes.

## Implementation Blueprint

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE archon-ui-main/src/components/agent-chat/hooks/useChatSession.ts
  - IMPLEMENT: Extract session initialization, streaming, and reconnection logic from ArchonChatPanel.
  
Task 2: CREATE archon-ui-main/src/components/agent-chat/hooks/usePanelResize.ts
  - IMPLEMENT: Extract mouse event listeners and width state calculation.

Task 3: CREATE archon-ui-main/src/components/agent-chat/components/ (Sub-components)
  - IMPLEMENT: ChatHeader.tsx, ChatMessageList.tsx, ChatInput.tsx
  - DEPENDENCIES: Accept props from the parent container.

Task 4: REFACTOR archon-ui-main/src/components/agent-chat/ArchonChatPanel.tsx
  - IMPLEMENT: Combine the new hooks and sub-components. Remove all heavy logic.

Task 5: CREATE archon-ui-main/src/features/knowledge/hooks/mutations/ (New Hooks)
  - IMPLEMENT: useCrawlMutations.ts, useUploadMutations.ts, useItemMutations.ts
  - DEPENDENCIES: Move specific useMutation blocks and import required optimistic utility functions.

Task 6: REFACTOR archon-ui-main/src/features/knowledge/hooks/useKnowledgeMutations.ts
  - IMPLEMENT: Remove all implementations and simply re-export from the new mutation hooks.
```

### Integration Points

```yaml
ROUTES/COMPONENTS:
  - All existing imports of `ArchonChatPanel` and `useKnowledgeMutations` MUST remain untouched. The refactoring must be entirely transparent to consumers.
```

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
cd archon-ui-main
pnpm run lint
```

## Final Validation Checklist

### Technical Validation
- [x] TypeScript checks pass (if `pnpm run typecheck` is available)
- [x] Linter passes: `cd archon-ui-main && pnpm run lint`

### Feature Validation
- [x] Chat panel resizes correctly.
- [x] Chat session connects and streams messages successfully.
- [x] Knowledge item mutations trigger optimistic UI updates without errors.

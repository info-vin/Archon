## 2025-03-05 - Button Accessibility Pattern
**Learning:** Found that custom buttons in the UI library rely on HTML `disabled` attribute but omitted `aria-disabled` and `aria-busy`. Screen readers benefit from explicitly mirroring these states, especially `aria-busy` for loading states to announce asynchronous operations properly.
**Action:** Always verify `aria-disabled` and `aria-busy` accompany visually disabled/loading components, particularly for reusable core components.
## 2026-07-14 - Redundant ARIA Labels on Buttons
**Learning:** Adding an `aria-label` to a button that already has visible text (like "Refine with AI") is often redundant or confusing, as screen readers will already read the button's inner text.
**Action:** When adding accessibility features to text-bearing buttons, prioritize state indicators (like `aria-busy` and `aria-disabled`) over `aria-label`, unless the visible text is completely non-descriptive. `aria-label` is best reserved for icon-only buttons.

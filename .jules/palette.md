## 2025-03-05 - Button Accessibility Pattern
**Learning:** Found that custom buttons in the UI library rely on HTML `disabled` attribute but omitted `aria-disabled` and `aria-busy`. Screen readers benefit from explicitly mirroring these states, especially `aria-busy` for loading states to announce asynchronous operations properly.
**Action:** Always verify `aria-disabled` and `aria-busy` accompany visually disabled/loading components, particularly for reusable core components.

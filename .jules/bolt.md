## 2026-02-19 - React Component Optimization
**Learning:** Moving static style objects outside of React components and using `React.memo` for leaf UI components (like Buttons) significantly reduces memory allocation and re-renders, especially in design systems with complex style maps.
**Action:** When auditing React components, look for large constant objects defined inside the render body and extract them.

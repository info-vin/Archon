## 2026-07-15 - Found Missing ARIA Loading States
**Learning:** Found that loading/disabled buttons (like the ClockInWidget button) often use standard HTML `disabled` but lack the corresponding `aria-disabled` and `aria-busy` attributes necessary for screen readers to announce loading states effectively. They also sometimes lack visible keyboard focus rings.
**Action:** Always verify that interactive loading states include `aria-busy` and `aria-disabled` alongside standard `disabled` and ensure `focus-visible` is implemented.
## 2026-07-28 - Missing Focus Rings on Modal Close Buttons
**Learning:** Discovered a consistent pattern where modal/drawer close buttons across multiple components (IdentityNewUserModal, ContentReviewPanel, LeadPitchDrawer, etc.) lacked keyboard focus indicators, breaking accessibility for keyboard users.
**Action:** When adding or reviewing interactive icon buttons, specifically those used for dismissal/closing overlays, always ensure `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2` are explicitly applied to the `className` for keyboard a11y.
## 2026-07-29 - Missing Focus Rings on Navigation Layout Buttons
**Learning:** Found that core layout navigational icon buttons (like the mobile menu toggles and user logout buttons in PublicLayout and MainLayout) lacked keyboard focus indicators. While they functioned on click, keyboard-only users could not visually identify when these critical navigational elements were focused.
**Action:** When adding or reviewing layout-level navigational buttons, always ensure `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring` (and optionally `focus-visible:ring-offset-2`) are explicitly applied to the `className` for keyboard a11y.

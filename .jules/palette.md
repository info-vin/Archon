## 2026-07-15 - Found Missing ARIA Loading States
**Learning:** Found that loading/disabled buttons (like the ClockInWidget button) often use standard HTML `disabled` but lack the corresponding `aria-disabled` and `aria-busy` attributes necessary for screen readers to announce loading states effectively. They also sometimes lack visible keyboard focus rings.
**Action:** Always verify that interactive loading states include `aria-busy` and `aria-disabled` alongside standard `disabled` and ensure `focus-visible` is implemented.
## 2026-07-28 - Missing Focus Rings on Modal Close Buttons
**Learning:** Discovered a consistent pattern where modal/drawer close buttons across multiple components (IdentityNewUserModal, ContentReviewPanel, LeadPitchDrawer, etc.) lacked keyboard focus indicators, breaking accessibility for keyboard users.
**Action:** When adding or reviewing interactive icon buttons, specifically those used for dismissal/closing overlays, always ensure `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2` are explicitly applied to the `className` for keyboard a11y.
## 2026-07-29 - Missing Focus Rings on Navigation Layout Buttons
**Learning:** Found that core layout navigational icon buttons (like the mobile menu toggles and user logout buttons in PublicLayout and MainLayout) lacked keyboard focus indicators. While they functioned on click, keyboard-only users could not visually identify when these critical navigational elements were focused.
**Action:** When adding or reviewing layout-level navigational buttons, always ensure `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring` (and optionally `focus-visible:ring-offset-2`) are explicitly applied to the `className` for keyboard a11y.
## 2026-08-01 - Missing Focus Rings on Inline Tag Removal Buttons
**Learning:** Found that inline interactive elements, specifically the 'Remove item' icon buttons inside selected knowledge tags (`KnowledgeSelector`), lacked keyboard focus indicators. These small buttons are easily missed but critical for keyboard navigation inside interactive form elements.
**Action:** When adding or reviewing inline tag components, always ensure the removal buttons have explicit focus rings (e.g., `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 rounded-sm`).
## 2026-08-05 - Missing Focus Rings on AudioPlayer Play/Pause Button
**Learning:** Found that the main play/pause button in `AudioPlayer` lacked keyboard focus indicators, breaking accessibility for keyboard users navigating audio content. Additionally, the button lacked an `aria-busy` attribute during loading states, which is important for screen reader context.
**Action:** When adding or reviewing interactive audio or media player controls, always ensure explicit focus rings (e.g., `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500`) are applied and `aria-busy` is utilized during asynchronous audio loading states.
## 2024-08-07 - Add focus visible styles to ActiveForce team member button
**Learning:** Found a pattern where icon-only action buttons inside mapped lists (like team member cards) often lack proper focus rings, hindering keyboard navigation for screen readers or power users.
**Action:** Always ensure mapped UI components with actionable elements have explicitly defined `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2` tailwind classes on them.

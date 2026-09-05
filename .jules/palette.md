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
## 2026-08-09 - Ensure Close Modal Buttons Have Focus Styles
**Learning:** Icon-only modal close buttons often miss focus indicators because default outline styles may have been globally removed or overridden, leading to poor keyboard accessibility. The standard `p-1 hover:bg-gray-200 rounded-full` pattern used across this application looks great on mouse interaction but provides zero feedback for keyboard users.
**Action:** When adding close buttons or reviewing existing ones, standardize on the application's established pattern for accessible focus rings on icon-only buttons: `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2`.
## 2026-08-09 - Missing Accessible Labels on Search Inputs
**Learning:** Found that search inputs (like in `SmartImagePicker.tsx` or `RAGPlayground.tsx`) often rely entirely on visual placeholders for context without an explicit, screen-reader-accessible label, breaking accessibility for non-visual users.
**Action:** When adding or reviewing search inputs or similar form controls without visible text labels, always ensure a `<label className="sr-only">` is properly associated with the input using `htmlFor` and `id` to provide context for screen readers.
## 2026-08-10 - Missing Accessible Labels on Search Inputs (KnowledgeSelector)
**Learning:** Found that the search input in `KnowledgeSelector.tsx` lacked an explicit, screen-reader-accessible label. Using `sr-only` class is good, but `aria-label` is safer to ensure it works independent of tailwind styles or layout changes and doesn't visually break things.
**Action:** When adding or reviewing search inputs or similar form controls without visible text labels, always ensure an `aria-label` is used if `sr-only` is not practical or might introduce layout issues.
## 2024-05-19 - Adding accessible labels to naked password inputs
**Learning:** In contexts like `ManageMemberModal`, password input fields were relying purely on `placeholder` text for identity. Placeholders are frequently skipped by screen readers or considered poor practice for accessible names.
**Action:** Always prefer adding an explicit `aria-label` directly to naked `<input>` elements over adding a `.sr-only` class label to prevent potential layout shifts and regression in the DOM, while maintaining 100% accessible naming.
## 2026-08-13 - Focus Styles on Action Buttons in BrandDashboardView
**Learning:** Found that the action buttons (edit, pro, review, publish, delete) in the Kanban columns on the BrandDashboardView lacked explicit focus rings. While these buttons are interactive and styled nicely for mouse hover states, they were completely invisible to keyboard navigation.
**Action:** Applied the application's standard `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2` to all action buttons in the BrandDashboardView Kanban feed list items.
## 2026-08-14 - Missing Focus Rings on Dashboard View Mode Toggles
**Learning:** Found that the primary view mode toggle buttons (list, table, kanban, gantt) and action buttons in the main Dashboard layout lacked clear keyboard focus indicators.
**Action:** When adding or reviewing layout-level navigational or toggle buttons, always ensure `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2` (or appropriate offset/color) are explicitly applied for keyboard accessibility.
## 2024-08-15 - Ensure hover-revealed elements are keyboard accessible
**Learning:** When using Tailwind utility classes like opacity-0 group-hover:opacity-100 to reveal interactive elements only on mouse hover, these elements become completely invisible and functionally unusable for keyboard-only users who tab through the interface.
**Action:** Always include a focus-within:opacity-100 or focus:opacity-100 utility class alongside the group-hover modifier so that the container becomes visible when any of its interactive child elements receive keyboard focus.
## 2024-08-16 - Add aria-pressed to toggle buttons
**Learning:** Filter buttons that act as toggles (e.g., 'All Leads' vs 'Review Queue') often lack state indicators. Screen reader users need to know which filter is currently active.
**Action:** Always add `aria-pressed={condition}` to button elements that function as stateful toggles in React.
## 2024-08-19 - Manager UI Keyboard Accessibility Focus States
**Learning:** While reviewing `ContentReviewPanel`, `ActiveForce`, and other manager components, it was observed that many interactive buttons (especially icon-only actions and state-toggling tabs) lacked visible focus indicators for keyboard users. Specifically, Tailwind classes `focus-visible:outline-none`, `focus-visible:ring-2`, and `focus-visible:ring-offset-2` were inconsistently applied.
**Action:** Applied a systematic sweep to ensure `focus-visible` ring styling is attached to actionable components to meet WCAG focus visibility standards without affecting mouse interactions.

## 2023-10-27 - 確保 ThemeToggle 按鈕具備 FocusVisible 狀態
**Learning:** Icon-only 按鈕或 Theme Toggles 通常只專注 hover 狀態，而忽略了鍵盤無障礙支援 (`focus-visible`)。這導致依賴鍵盤瀏覽的用戶無法辨識焦點。
**Action:** 所有互動元件均須包含 `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2`，以符合 a11y 規範。
## 2026-08-21 - Ensure Clickable Containers have Keyboard Support
**Learning:** Found that custom clickable components acting as buttons (like `AiCollaborationWidget` which uses `onClick` on a generic `div`) lack keyboard support (Enter/Space to trigger, `tabIndex`, `role`). This makes them inaccessible to keyboard users, even if focus rings are applied.
**Action:** When adding `onClick` to a non-interactive element like a `div` to make it behave like a button, always add `role="button"`, `tabIndex={0}`, an `onKeyDown` handler for 'Enter' and ' ', and appropriate ARIA labels along with `focus-visible` styling.
## 2026-08-22 - Missing Focus Rings on Team Member Action Buttons
**Learning:** Found that primary action buttons in mapped lists (like Manage Role, View Activity in `TeamMemberCard.tsx`) often lack proper keyboard focus rings despite having extensive mouse hover state styling. This leaves keyboard users without visual indicators on major interaction points.
**Action:** Always verify that actionable elements within card components or lists include explicit `focus-visible` states like `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2`.
## 2024-05-15 - Dynamic ARIA Labels in Date Pickers
**Learning:** Screen reader users need dynamic context for highly interactive components like Date/Time pickers. Static labels like "Set Date" are insufficient once a date is selected. Presets (like "Tomorrow" or "+3 Days") need explicit explanatory text, as their relative nature might not be clear out of visual context.
**Action:** Always ensure that trigger buttons for complex custom widgets (like modal pickers) dynamically update their `aria-label` to reflect the currently selected value.
## 2024-08-24 - Add Keyboard Focus Indicators
**Learning:** Found multiple interactive buttons lacking visible focus indicators. While hover states existed, keyboard users would not see what was focused. Using `focus-visible:outline-none focus-visible:ring-2` combined with offset rings is highly effective and simple to implement in Tailwind, greatly improving a11y across the site.
**Action:** Always include `focus-visible` classes by default when creating custom buttons or interactive elements in this app's components, as standard hover classes do not cover keyboard navigation.
## 2026-08-25 - Improved Keyboard Accessibility for Task Lists
**Learning:** In list and kanban views (e.g., `ListView.tsx`, `KanbanView.tsx`, `TableView.tsx`), rows and cards acting as buttons lacked native keyboard focus and interaction support. Hover states alone do not provide a visible focus indicator for screen readers and keyboard users.
**Action:** When implementing custom interactive lists or cards, always add `tabIndex={0}`, `role="button"`, `aria-label`, a visible focus ring (`focus-visible:ring-2`), and an `onKeyDown` handler to support Enter/Space key navigation.
## 2024-05-24 - Add focus-visible to icon-only buttons
**Learning:** Icon-only buttons often lack visual indicators for keyboard users when focused, causing accessibility issues. Adding `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2` provides necessary feedback for keyboard navigation.
**Action:** Always check icon-only buttons for focus visibility and add necessary Tailwind classes when improving a11y.
## 2026-08-28 - Missing Accessible Labels on action buttons with text and icons
**Learning:** Action buttons that contain both text and icons (e.g., "Copy Text" and "Share" in `LeadPitchDrawer.tsx`) sometimes lack explicit `aria-label` attributes. While the text provides visual context, ensuring screen readers announce the action clearly is important for full accessibility, especially if the text changes based on state (e.g., "Copied").
**Action:** When adding or reviewing action buttons, consider adding an explicit `aria-label` to provide a clear and consistent accessible name, even if there is text present, to ensure robust screen reader support.

## 2025-02-27 - Add keyboard focus indicators to Brand Hub controls
**Learning:** Found that custom or native buttons in `BrandPage.tsx` such as the "Refresh", "Close modal", and "Save changes" buttons were missing adequate or complete `focus-visible` outline styles, which decreases keyboard navigation accessibility.
**Action:** Applied standard `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2` to these buttons. Will continue explicitly reviewing interactive element states (focus, disabled, active) when inspecting or implementing custom modals and header controls.
## 2024-03-24 - [Add aria-pressed to Marketing Page Tab Buttons]
**Learning:** Found that custom tab buttons in `enduser-ui-fe/src/pages/MarketingPage.tsx` rely solely on visual styling (color classes) to indicate active state, lacking proper `aria-pressed` or `aria-selected` attributes for screen readers. They also missed `focus-visible` classes for keyboard navigation.
**Action:** Always verify that custom tab-like buttons use `aria-pressed={isActive}` or role="tab" with `aria-selected={isActive}`. Ensure `focus-visible` styles are added for keyboard accessibility.
## 2024-10-27 - Add ARIA attributes to mobile menu toggle
**Learning:** The mobile sidebar toggle button in `MainLayout.tsx` was relying solely on visual icons and a small text span to convey its purpose, which is insufficient for screen readers navigating dynamic menus. It lacked state tracking.
**Action:** When creating toggle buttons that control expanding/collapsing sections (like sidebars or accordions), always include `aria-expanded` tied to the state variable, and `aria-controls` pointing to the ID of the controlled element.
## 2024-05-15 - Preserve Focus Styles with Custom ClassNames
**Learning:** When React components accept a custom `className` prop, defaulting with `??` can accidentally overwrite critical accessibility classes like `focus-visible`, leading to a loss of keyboard focus indicators when the component is composed.
**Action:** Always extract essential utility classes (like focus outlines) into a base string and conditionally append them alongside the provided `className`.

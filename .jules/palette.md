## 2025-03-03 - Accessible Icon-Only Buttons
**Learning:** Adding `aria-label` and `title` to icon-only buttons drastically improves accessibility for screen readers and provides helpful tooltips for sighted users. Grouping them with `role="group"` and `aria-label="View mode"` provides better context.
**Action:** Always check icon-only buttons for missing accessible labels and apply `aria-label` and `title` attributes. For grouped controls, use `role="group"`. When unit testing these in `enduser-ui-fe`, remember to wrap them in `<AuthProvider>` and properly mock the api and supabase client to avoid render failures.

## 2025-03-03 - Missing ARIA Labels on Close Modals
**Learning:** Icon-only close buttons (`XIcon`) across various feature components (`ContentWorkbench`, `ManagerNexus`, `LeadsCardStack`, `BrandWorkbenchView`) frequently lack `aria-label` attributes, causing them to be announced simply as "button" by screen readers.
**Action:** When implementing modal or panel close actions using `XIcon` or similar icon-only buttons, always explicitly add an `aria-label` attribute (e.g., `aria-label="Close modal"` or a more descriptive label like `aria-label="Close AI Command Center"`).

## 2025-05-14 - Adding ARIA labels to grouped icon-only buttons
**Learning:** Icon-only buttons lacking `aria-label`s fail to convey their purpose to screen reader users. When these buttons act as a group (e.g., action buttons for a task), wrapping them in an element with `role="group"` and an `aria-label` provides crucial context.
**Action:** Always add `aria-label` to icon-only buttons. If they are logically grouped, enclose them in a container with `role="group"` and an `aria-label`.

## 2026-04-02 - [Dynamic ARIA labels for loading states]
**Learning:** Screen readers might not correctly announce the changing state of a button if its inner text changes during async operations (like from 'Reconnect' to 'Connecting...').
**Action:** Always provide a dynamic `aria-label` that reflects the current loading state of the button.

## 2025-03-05 - ActiveForce Member Details Button Accessibility
**Learning:** Icon-only buttons used for viewing specific item details (like team members) need dynamic ARIA labels that include the item's name (e.g., `aria-label={\`View details for \${member.name}\`}`) to provide adequate context for screen reader users, rather than a generic "View details".
**Action:** Always use dynamic interpolation for `aria-label`s on icon-only buttons within mapped lists to ensure context-specific accessibility.

## 2024-04-22 - Replacing Hardcoded Text Icons with Proper SVG Components
**Learning:** Hardcoded text characters (like `✕` for close buttons) not only look inconsistent across different OS and fonts, but they also severely harm accessibility if lacking an `aria-label`. Screen readers may read out the literal character name (e.g., "multiplication x"), which is confusing.
**Action:** When creating or fixing modal close buttons, always use existing SVG icon components (like `<XIcon />`) from the design system, and explicitly attach a descriptive `aria-label` (e.g., `aria-label="Close modal"`) to ensure the intent is clearly communicated to assistive technologies.

## 2024-05-18 - Expanding Generic Component Props for Accessibility
**Learning:** Reusable UI components like custom Checkboxes and Toggles often encapsulate standard HTML elements but omit crucial accessibility props (like `aria-label`). If a developer uses `<Checkbox />` without a visible `<label>`, screen readers have no context for what the checkbox controls.
**Action:** Always inspect custom UI primitives to ensure they can accept and forward `aria-label` or `aria-labelledby` props. When creating generic components, include `ariaLabel?: string;` in the props interface and apply it to the underlying interactive element, ideally with a fallback if appropriate.
## 2025-05-19 - Multiline Scanning for Accessibility Attributes
**Learning:** Standard line-by-line grep fails to identify missing `aria-label`s on `<button>` elements that span multiple lines, leaving hidden accessibility gaps in JSX code.
**Action:** When auditing the codebase for missing attributes, use multiline regex scripts (e.g., Python `re.findall(r'<button[^>]*>[\s\S]*?</button>', content)`) to correctly parse and validate components structured across multiple lines.

## 2024-05-03 - Contextual ARIA labels in mapped arrays
**Learning:** When using generic icon-only buttons (like "Delete", "View", or "Like") inside a list or a grid of identical cards, screen readers will read identically named elements consecutively (e.g. "View Timeline", "View Timeline"). This provides no context as to *which* element the action applies to.
**Action:** Always use dynamic interpolation when inside of `.map()` lists or components representing a generic child (e.g., `LeadCard.tsx`) so that the `aria-label` includes the uniquely identifying information (like `${lead.company_name}` or `${user.name}`).

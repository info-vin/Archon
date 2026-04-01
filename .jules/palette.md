## 2025-03-03 - Accessible Icon-Only Buttons
**Learning:** Adding `aria-label` and `title` to icon-only buttons drastically improves accessibility for screen readers and provides helpful tooltips for sighted users. Grouping them with `role="group"` and `aria-label="View mode"` provides better context.
**Action:** Always check icon-only buttons for missing accessible labels and apply `aria-label` and `title` attributes. For grouped controls, use `role="group"`. When unit testing these in `enduser-ui-fe`, remember to wrap them in `<AuthProvider>` and properly mock the api and supabase client to avoid render failures.

## 2025-03-03 - Missing ARIA Labels on Close Modals
**Learning:** Icon-only close buttons (`XIcon`) across various feature components (`ContentWorkbench`, `ManagerNexus`, `LeadsCardStack`, `BrandWorkbenchView`) frequently lack `aria-label` attributes, causing them to be announced simply as "button" by screen readers.
**Action:** When implementing modal or panel close actions using `XIcon` or similar icon-only buttons, always explicitly add an `aria-label` attribute (e.g., `aria-label="Close modal"` or a more descriptive label like `aria-label="Close AI Command Center"`).

## 2025-05-14 - Adding ARIA labels to grouped icon-only buttons
**Learning:** Icon-only buttons lacking `aria-label`s fail to convey their purpose to screen reader users. When these buttons act as a group (e.g., action buttons for a task), wrapping them in an element with `role="group"` and an `aria-label` provides crucial context.
**Action:** Always add `aria-label` to icon-only buttons. If they are logically grouped, enclose them in a container with `role="group"` and an `aria-label`.

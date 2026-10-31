# Palette Accessibility & UX Guidelines (Consolidated)

## 1. Explicit Button Types and Focus-Visible Rings
**Learning:** `<button>` elements without an explicit `type` default to `type="submit"`, risking accidental form submissions (form hijacking) inside modals and panels. Additionally, icon-only and custom action buttons frequently lack visible keyboard focus indicators.
**Action:** Always declare `type="button"` on non-submit buttons and include `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2` for keyboard accessibility.

## 2. Keyboard Support and WAI-ARIA for Custom Interactive Elements
**Learning:** Non-interactive elements (`div`, `span`, table headers, Kanban cards) with `onClick` handlers are invisible to keyboard navigation, and custom tabs or collapsible sections break screen reader context without ARIA state linking.
**Action:** Pair custom clickable containers with `role="button"`, `tabIndex={0}`, and Enter/Space `onKeyDown` handlers. Use `aria-expanded` + `aria-controls` for disclosures, `aria-pressed` for stateful toggles, and full WAI-ARIA `role="tab"` / `role="tabpanel"` mappings for tabs.

## 3. Accessible Naming Without Violating WCAG 2.5.3 (Label in Name)
**Learning:** Relying solely on `placeholder` text for search/password inputs leaves screen readers without context, whereas adding an arbitrary `aria-label` to a button that already has clear visible text overrides the visible label and breaks voice control.
**Action:** Provide explicit `aria-label` (or `<label className="sr-only">`) for icon-only buttons and unlabeled inputs, inject dynamic item names in repeated list actions (e.g., `Remove ${item.name}`), and never override clear visible button text with a conflicting `aria-label`.

## 4. Loading States, Hover-Revealed Controls, and Decorative Icons
**Learning:** Asynchronous buttons using only `disabled` fail to announce loading progress to screen readers, `opacity-0 group-hover:opacity-100` hides actions from keyboard users, and decorative SVGs clutter the accessibility tree.
**Action:** Add `aria-busy` and `aria-disabled` during loading states, pair `group-hover:opacity-100` with `focus-within:opacity-100`, and mark purely decorative icons with `aria-hidden="true"`.

## 2026-10-31 - Escape Key Dismissal and WAI-ARIA Dialog Semantics on Custom Modals
**Learning:** Custom overlay modals without `role="dialog"`, `aria-modal="true"`, and `aria-labelledby` fail to inform screen readers of their modal nature, and lacking an `Escape` key listener traps keyboard users into tabbing through all inputs to reach a close button. Furthermore, error messages without `role="alert"` and `aria-live="polite"` go unnoticed by non-visual users.
**Action:** Always wrap modal panels with `role="dialog"`, `aria-modal="true"`, and `aria-labelledby`, attach an `Escape` key listener on the modal overlay or window, and mark dynamic validation errors with `role="alert"` and `aria-live="polite"`.

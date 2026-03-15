💡 **What:**
Added `aria-label` and `title` attributes ("Close modal") to the `<X>` icon-only close button in `OllamaModelSelectionModal.tsx`.

🎯 **Why:**
Icon-only buttons without accessible names cannot be interpreted by screen readers, making it difficult or impossible for visually impaired users to know how to close the modal. Adding a `title` attribute also provides a helpful tooltip for mouse users, clarifying the button's action before they click.

📸 **Before/After:**
*(See attached verification snapshot from Playwright for the visual state - visually identical, but semantically accessible).*

♿ **Accessibility:**
Fixes a critical WCAG gap (Missing ARIA label / Name, Role, Value) by explicitly naming the interactive element "Close modal".

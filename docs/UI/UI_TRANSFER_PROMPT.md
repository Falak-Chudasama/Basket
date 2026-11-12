# UI Design System Transfer Prompt

> **Instructions for the User:** Copy and paste the prompt below into the AI coding agent working on your target React application. Provide the accompanying files `UI_TRANSFER_SPEC.md`, `ui-design-tokens.json`, and `docs/screenshots/` in the agent's workspace.

---

```markdown
# TASK: Apply the Kiwi Apple-Grade Design System to this Application

You are acting as the **Principal Design Systems Architect, Lead Staff Frontend Engineer, and UI/UX Quality Specialist**.

Your assignment is to elevate the visual presentation, typography, component styling, layout architecture, and interaction design of this React codebase so that it matches the exact aesthetic identity and tactile Apple-grade quality defined in the **Kiwi UI Design System**.

You are provided with three reference deliverables:
1. `UI_TRANSFER_SPEC.md` — The complete design manual, component specifications, page layouts, interaction states, and implementation recipes.
2. `ui-design-tokens.json` — The validated, machine-readable source of truth for colors, typography, radii, shadows, animations, and spacing.
3. `screenshots/` — 47 real browser-rendered screenshots demonstrating authentic desktop, tablet, and mobile layouts across both Light and Dark modes.

Treat these files as the absolute source of truth for all visual and styling decisions.

---

## 1. Prime Directives & Transferability Rules

### A. Preserve Existing Business Logic & Functional Integrity
- **Do not modify, mock, or break the target application's functionality:** Retain all existing state management, API routes, data structures, event handlers, client-side algorithms, authentication flows, and domain-specific features.
- Your task is an aesthetic and design-system elevation, not a functional rewrite.

### B. Product Identity vs. Design System Conventions
- **DO NOT force Kiwi's fruit branding onto the target product:**
  - If the target application is a financial dashboard, developer tool, healthcare portal, or CRM, keep its genuine product name, logo, domain terms, and purpose.
  - Do not substitute the target application's logo with a kiwi fruit SVG unless explicitly instructed.
- **DO adopt Kiwi's transferable design-system conventions:**
  - **The "Quiet Utility" Aesthetic:** Calm, low-saturation canvas (`#F8F9F5` in light, `#121310` in dark) instead of stark white or generic blue-gray.
  - **Strict Typographic Separation:** A distinct geometric display typeface for hero headers and brand wordmarks (`Unbounded` or equivalent geometric display face), paired with an exceptionally clean sans-serif for all UI body text, buttons, navigation, and inputs (`Host Grotesk` or equivalent neo-grotesque).
  - **Selective Glassmorphism:** Glass (`backdrop-filter: blur()`) is strictly reserved for floating chrome (the top floating navigation capsule, mobile bottom dock, action sheets, and modal backdrops). All working cards use solid or near-solid elevated surfaces to guarantee crisp legibility and 60fps performance.
  - **Adaptive Dual-Mode Navigation:** A floating pill capsule on desktop (`≥ 640px`) transforming into a sticky top bar and fixed floating bottom dock on mobile (`< 640px`).
  - **Two-Tier Focus Ring:** Accessible, distinct 2px outer + 2px inner focus ring on all interactive elements.

---

## 2. Step-by-Step Implementation Workflow

### Step 1: Design Tokens & Font Setup
1. Inspect `ui-design-tokens.json`.
2. Configure local `@font-face` definitions for the primary UI typeface (`Host Grotesk` or equivalent) and display typeface (`Unbounded` or equivalent). Do not load remote fonts from Google Fonts or external CDNs.
3. Update Tailwind configuration (`tailwind.config.ts`) with:
   - `darkMode: 'class'`
   - Extended brand color palette (primary accent, secondary accent, neutral canvas ladder).
   - Border radii (`card: 1.25rem`, `capsule: 9999px`).
   - Layered box shadows (`2xs`, `xs`, `soft`, `lift`, `floating`).
   - Animations & keyframes (`fade-in: 0.15s ease-out`, `scale-in: 0.18s cubic-bezier(0.16, 1, 0.3, 1)`, `slide-up: 0.18s ease-out`).

### Step 2: Global Shell & Zero-Flash Theme Engine
1. Implement a `ThemeProvider` managing `'light' | 'dark'` modes, persisting to `localStorage.getItem('theme')`, synchronizing the `.dark` class on `document.documentElement`, and listening to OS `(prefers-color-scheme: dark)`.
2. Inject a lightweight inline script in `index.html`'s `<head>` to prevent flash-of-light-mode (FOIT/FOUC) on page reload.
3. Set the global main container to `max-w-4xl mx-auto px-4 py-8 pb-24 sm:py-12 sm:pb-16`.

### Step 3: Navigation Architecture
1. **Desktop (`sm:block`):** Floating navigation capsule (`sticky top-4 z-40 mx-auto max-w-4xl px-4`) featuring:
   - Brand logo and wordmark on the left.
   - Navigation links in the center (`rounded-full px-4 py-2 text-sm font-semibold`). Active links receive `bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs`.
   - Subtle vertical divider (`h-5 w-px bg-stone-200 dark:bg-stone-700 mx-1`).
   - Theme toggle button with animated Sun/Moon icons on the right.
2. **Mobile (`sm:hidden`):**
   - Sticky top bar (`sticky top-0 z-40 border-b bg-white/95 dark:bg-[#181915]/95 backdrop-blur-md px-5 py-3.5`).
   - Fixed floating bottom dock (`fixed bottom-3 inset-x-3 z-50 rounded-2xl border bg-white/95 dark:bg-[#181915]/95 shadow-lift backdrop-blur-lg py-2.5 px-2 flex justify-around`).

### Step 4: Component-by-Component Upgrade
Consult Section 8 of `UI_TRANSFER_SPEC.md` and upgrade each UI element in the target codebase:
1. **Content Cards:** Convert generic cards to `rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-white dark:bg-[#181915] p-6 shadow-soft`.
2. **Primary Buttons:** Style as `rounded-2xl bg-brand hover:bg-brand-dark text-white font-bold px-8 py-3.5 shadow-soft focus-ring transition`.
3. **Form Inputs:** Upgrade inputs and search fields to `rounded-xl border border-stone-200/90 dark:border-white/[0.08] bg-white dark:bg-[#181915] px-4 py-3 text-stone-900 dark:text-stone-100 placeholder:text-stone-400 dark:placeholder:text-stone-500 focus-ring`.
4. **Lists / Chips:** Wrap items in `FileChip`-style rows with category-specific colored badges, truncated titles, metadata labels, and subtle remove buttons.
5. **Selection Grids / Pills:** Active items take solid fills with white text and focus rings; inactive items use subtle neutral stone borders with soft hover backgrounds.
6. **Progress & Modals:** Use `ProgressPanel` with smooth animated track fills, and `Popup` with backdrop blur (`backdrop-blur-sm`), ESC-key dismissal, and scroll lock.

### Step 5: Responsive Verification
1. Test and verify all routes at the 8 standard viewports:
   - `360 × 800` (Small Mobile)
   - `390 × 844` (Modern Mobile)
   - `640 × 900` (Breakpoint boundary `sm`)
   - `768 × 1024` (Tablet Portrait `md`)
   - `1024 × 768` (Tablet Landscape `lg`)
   - `1366 × 768` (Standard Laptop)
   - `1440 × 900` (Desktop)
   - `1920 × 1080` (Large Desktop)
2. Verify that there is zero horizontal scroll or layout overflow at any width.
3. Toggle between Light and Dark mode on every page to ensure pristine contrast and legibility.
4. Run all type checks, unit tests, and build commands before declaring completion.
```


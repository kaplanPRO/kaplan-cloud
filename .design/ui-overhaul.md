# Kaplan Cloud — UI Overhaul Design Document

**Status:** In progress · S3 complete, S4 next
**Last updated:** 2026-04-18
**Branch:** `claude/ui-overhaul-planning-ZlwnV`

---

## Table of Contents

1. [Background & Goals](#1-background--goals)
2. [Current State Audit](#2-current-state-audit)
3. [Competitive Analysis](#3-competitive-analysis)
4. [Design Direction](#4-design-direction)
5. [Design Tokens](#5-design-tokens)
6. [Component Inventory](#6-component-inventory)
7. [Recommended Tech Stack](#7-recommended-tech-stack)
8. [Accessibility Goals](#8-accessibility-goals)
9. [Session Roadmap](#9-session-roadmap)

---

## 1. Background & Goals

Kaplan Cloud is a functional Django-based translation management system. The UI was built with a "wireframe-first" approach: raw Django `form.as_table`, hand-rolled vanilla CSS Grid, no component system, and no coherent design language. It works, but feels unfinished.

### Goals

- Establish a consistent, polished visual identity across all screens
- Adopt a component system that reduces per-screen CSS authorship
- Support both **light and dark themes** with a user-controlled toggle
- Remain **tablet-friendly** (desktop-primary, usable on tablets ≥768px)
- Preserve all existing editor functionality (keyboard shortcuts, TM integration, contenteditable logic)
- Produce a design document before touching code, so future sessions are well-scoped

### Non-goals (this overhaul)

- Full mobile (phone) support
- Real-time collaboration features
- Redesigning data models or backend logic
- Replacing the editor's JavaScript behavior (only reskin it)

---

## 2. Current State Audit

### Template inventory

| Template | Extends | Purpose |
|---|---|---|
| `base.html` | — | Root: DOCTYPE, CDN links, `{% block head %}`, `{% block body %}` |
| `index.html` | `base.html` | Dashboard shell: sidebar nav + main content area |
| `projects.html` | `index.html` | Projects list with searchable/filterable table |
| `project.html` | `index.html` | Project detail: file table, reference files, reports |
| `newproject.html` | `index.html` | Project creation form |
| `translation-memories.html` | `index.html` | TM list table |
| `tm.html` | `index.html` | TM detail: source/target entry table |
| `newtm.html` | `index.html` | TM creation form |
| `tm-import.html` | `index.html` | TM import form |
| `accounts/login.html` | `base.html` | Login form |
| `accounts/register.html` | `base.html` | Registration form |
| `accounts/change-password.html` | `base.html` | Password change form |
| `editor.html` | *(standalone)* | Full-page translation editor |
| `report.html` | *(standalone)* | Translation analysis report |

`editor.html` and `report.html` do **not** extend `base.html` — they are self-contained pages with their own CSS links.

### Static file inventory

| File | Lines | Purpose | Status |
|---|---|---|---|
| `main.css` | 236 | Global layout (CSS Grid shell, nav, buttons, modals, toasts, tables) | **Removed in S2** — caused global selector conflicts with daisyUI; `@layer legacy` wrapping was attempted but ineffective (Tailwind v4 also uses `@layer` internally) |
| `editor.css` | 151 | Editor-specific styles (3-col grid, segment rows, sidebars, filter dropdown) | To migrate in S5 |
| `main.js` | 5 | Search form toggle on Projects/TMs pages | To replace with Alpine `x-show` in S3 |
| `editor.js` | 681 | Full editor logic: contenteditable, TM/comment lookups, propagation, keyboard shortcuts, submission workflow | Preserved as-is |
| `project.js` | 242 | Project page: checkbox selection, context menus, file operations, linguist assignment | Minimal updates in S3 |
| `newproject.js` | 33 | Dynamic TM dropdown population via Fetch | No changes needed |

### Third-party dependencies (current)

| Library | Delivery | Used for |
|---|---|---|
| Google Material Icons | CDN | Nav icons, button icons, editor controls |
| Ubuntu (Google Fonts) | CDN | Global typeface |

No npm, no build step, no JS framework.

### UI component patterns (current)

- **Layout:** CSS Grid for sidebar + content shell; 3-column grid in editor
- **Navigation:** Vertical sidebar with `<ul>` items; horizontal header bar
- **Tables:** Raw `<table>` with manual `oddrow`/`evenrow` classes; no pagination component
- **Forms:** Django `form.as_table` — every form is a `<table>`, not styled intentionally
- **Modals:** Hand-rolled overlay (fixed-position backdrop + centered box via CSS Grid)
- **Context menus:** Absolutely-positioned `<div>` revealed by JS class toggle
- **Toasts:** Fixed-position `<div>` with `fadeIn` CSS animation
- **Status badges:** Inline styles or class names (`translated`, `draft`, `blank`, `error`, `reviewed`, `locked`)
- **Theme:** Dark only (`#2a2f33` background, `#f5f5f5` text)

---

## 3. Competitive Analysis

### Lokalise

**Aesthetic:** Clean SaaS, content-first. The reference for this overhaul.
**Layout:** Left sidebar navigation (collapsible), wide main content area, top header for account/settings.
**Color:** Light-first with strong dark mode. Neutral grays, single blue primary (`#5C6BC0`-range), high-contrast text.
**Typography:** Inter (or system font stack), consistent size scale, no decorative type.
**Components:** Card-based project lists, full-width data tables with row actions, clean modal dialogs, inline status chips.
**Icons:** Custom SVG icon set — flat, monochrome, consistent stroke weight.
**Notable patterns:** Screenshot context for translators; filter/search always visible above tables; subtle hover states on rows.

### Phrase (Memsource)

**Aesthetic:** Power-user dense — optimizes for information at a glance over polish.
**Editor layout:** Source segment (left) / target segment (right) table, status column, TM/glossary/comments in right panel.
**Controls:** Status bar at bottom with word count, file name, user; toolbar above editor for spellcheck, find/replace.
**Notable patterns:** Segment status color column (not the full row), desktop-first.

### Crowdin

**Aesthetic:** More consumer-friendly than Phrase; feature-rich but visually lighter.
**Editor modes:** Side-by-side, comfortable, multilingual, multilingual-grid — user-selectable.
**Themes:** Light, dark, and auto-detect; JSON-configurable custom themes; a theme-builder app.
**Notable patterns:** Dual-preview (WYSIWYG source + translation); context pane + AI panel + glossary + comments in right sidebar tabs.

### Common TMS/CAT conventions

These patterns appear across all major tools and should be preserved or improved in Kaplan Cloud:

- **Segment table:** source/target columns, status indicator column, segment ID
- **Right sidebars:** TM matches, glossary/termbase, comments — tabbed or stacked
- **Status color coding:** distinct colors per state (translated, draft, blank, locked, error, reviewed)
- **Keyboard-first editor:** Tab to advance, Ctrl+Enter to confirm, F3 for concordance
- **Filter bar above segment list:** All / Translated / Draft / Blank / Error
- **Match percentage display:** color-coded (100% = green, fuzzy = amber, no match = zinc)
- **Toast notifications:** non-blocking, auto-dismiss, bottom-right or top-right

---

## 4. Design Direction

### Aesthetic

**Neo-minimalist SaaS** — Lokalise is the primary reference. Clean, content-first, warm neutrals. Professional but approachable. Not sterile, not dark-hacker.

- Light mode is the default; dark mode is fully supported via user toggle
- Whitespace is generous but not wasteful
- Color is used intentionally: one primary accent, semantic colors for status, neutrals everywhere else
- Icons are flat SVG (Heroicons), consistent 20px/24px stroke weight
- No decorative gradients, shadows are subtle (not card-heavy)

### Typography

**Inter** via CDN (replacing Ubuntu). Reason: Inter is purpose-designed for UI at small sizes; it's the de-facto standard for modern SaaS and is free.

| Role | Size | Weight |
|---|---|---|
| Page heading (h1) | 24px / 1.5rem | 600 |
| Section heading (h2) | 18px / 1.125rem | 600 |
| Body / table text | 14px / 0.875rem | 400 |
| Caption / meta | 12px / 0.75rem | 400 |
| Button | 14px / 0.875rem | 500 |
| Segment source text | 15px / 0.9375rem | 400 |
| Segment target text | 15px / 0.9375rem | 400 |

### Icons

Replace **Google Material Icons** with **Heroicons** (MIT, no CDN dependency, SVG sprites). Heroicons are the native icon set for Tailwind / daisyUI projects.

---

## 5. Design Tokens

### Color palette

#### Neutral scale (Zinc — used for backgrounds, borders, text)

| Token | Light value | Dark value | Hex (light) | Hex (dark) |
|---|---|---|---|---|
| `bg-base` | zinc-50 | zinc-900 | `#fafafa` | `#18181b` |
| `bg-surface` | white | zinc-800 | `#ffffff` | `#27272a` |
| `bg-subtle` | zinc-100 | zinc-700 | `#f4f4f5` | `#3f3f46` |
| `border` | zinc-200 | zinc-700 | `#e4e4e7` | `#3f3f46` |
| `border-strong` | zinc-300 | zinc-600 | `#d4d4d8` | `#52525b` |
| `text-primary` | zinc-900 | zinc-50 | `#18181b` | `#fafafa` |
| `text-secondary` | zinc-500 | zinc-400 | `#71717a` | `#a1a1aa` |
| `text-disabled` | zinc-400 | zinc-600 | `#a1a1aa` | `#52525b` |

#### Brand color

The app logo uses **`#f84000`** (flame orange-red, hue 15.5°, saturation 100%). This is used only as a brand mark — in the logo and favicon. It is **not** a UI interactive color.

Constraints this imposes on the rest of the palette:
- Primary accent must not be indigo (contrast ratio 1.71 — near-complementary at similar luminance, creates visual noise)
- Amber must not be used for segment status (hue only ~25° away from logo — will bleed into brand color visually)
- Any interactive blue/teal reads cleanly against the logo and doesn't compete with it

#### Primary accent (Teal)

Teal was chosen because: (a) it pairs naturally with warm orange-red logos (split-complementary harmony), (b) no major TMS competitor uses teal as their primary — it's distinctive, and (c) it passes WCAG AA on both light and dark surfaces.

| Token | Value | Hex |
|---|---|---|
| `primary` | teal-600 | `#0d9488` |
| `primary-hover` | teal-700 | `#0f766e` |
| `primary-subtle` | teal-50 | `#f0fdfa` |
| `primary-text` | white | `#ffffff` |

Dark mode uses the same primary values — teal-600 reads well on zinc-900.

#### Semantic: segment status

`reviewed` moves from teal to emerald (teal is now the primary interactive color — using it for status too would create ambiguity). `draft` moves from amber to yellow — amber sits at hue ~38°, only 23° from the logo's 15.5°; yellow at hue ~60° is sufficiently distinct.

| Status | Color name | Light bg hex | Light text hex | Dark bg hex | Dark text hex |
|---|---|---|---|---|---|
| `translated` | Green | `#dcfce7` | `#15803d` | `#14532d` | `#86efac` |
| `reviewed` | Emerald | `#d1fae5` | `#065f46` | `#064e3b` | `#6ee7b7` |
| `draft` | Yellow | `#fefce8` | `#854d0e` | `#422006` | `#fef08a` |
| `blank` | Zinc | `#f4f4f5` | `#52525b` | `#27272a` | `#a1a1aa` |
| `locked` | Violet | `#ede9fe` | `#6d28d9` | `#2e1065` | `#c4b5fd` |
| `error` | Red | `#fee2e2` | `#b91c1c` | `#450a0a` | `#fca5a5` |

#### Semantic: TM match percentage

| Match | Color name | Hex |
|---|---|---|
| 100% (exact) | Green-600 | `#16a34a` |
| 95–99% | Lime-600 | `#65a30d` |
| 85–94% | Amber-500 | `#f59e0b` |
| 75–84% | Orange-500 | `#f97316` |
| 50–74% | Red-400 | `#f87171` |
| New / no match | Zinc-400 | `#a1a1aa` |

#### Functional colors

| Token | Hex | Use |
|---|---|---|
| `success` | `#16a34a` | Positive feedback, success toasts |
| `warning` | `#d97706` | Warnings, partial matches |
| `danger` | `#dc2626` | Destructive actions, error states |
| `info` | `#2563eb` | Informational toasts, tips |

### Spacing scale

Uses Tailwind's default 4px base unit. No custom spacing tokens needed.

### Border radius

| Token | Value | Use |
|---|---|---|
| `rounded-sm` | 4px | Inputs, badges, small elements |
| `rounded-md` | 6px | Buttons, cards, panels |
| `rounded-lg` | 8px | Modals, larger surfaces |
| `rounded-full` | 9999px | Avatars, pill badges |

### Shadows

Minimal shadow usage — only for modals and popovers.

| Token | Value |
|---|---|
| `shadow-sm` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` |
| `shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1)` |
| `shadow-modal` | `0 20px 25px -5px rgb(0 0 0 / 0.1)` |

---

## 6. Component Inventory

Each component below describes its current implementation, the proposed implementation, and any notes.

### Shell / layout

**Current:** CSS Grid (`#main-content` grid with sidebar + content, hardcoded `#2a2f33` background)
**Proposed:** Tailwind `flex`/`grid` layout utilities; `bg-zinc-50 dark:bg-zinc-900` on `<body>`; sidebar width via Tailwind class (`w-56`)
**Notes:** The sidebar collapse state (currently missing) should be managed by Alpine `x-data` + `localStorage`

### Sidebar navigation

**Current:** `<ul>` with custom CSS, icons via Material Icons, several items hardcoded as disabled
**Proposed:** Tailwind-styled `<nav>`, Heroicons inline SVGs, active state via Django template tag or URL match, Alpine for collapse
**Items:** Projects, Translation Memories, Termbases (placeholder), Linguists (placeholder), Clients (placeholder)

### Header / top bar

**Current:** Horizontal bar with login/logout, settings, file analysis button; raw HTML
**Proposed:** Tailwind flex row with right-aligned actions; daisyUI `dropdown` for user menu; breadcrumb for current project/file context in editor

### Data tables

**Current:** Raw `<table>` with manual `oddrow`/`evenrow` classes
**Proposed:** daisyUI `table` class + Tailwind hover states (`hover:bg-zinc-50 dark:hover:bg-zinc-800`); row actions via Alpine dropdown
**Notes:** Checkbox selection in project.html stays; master checkbox JS logic preserved

### Forms

**Current:** `form.as_table` — every form renders as an HTML table
**Proposed:** Replace `form.as_table` with manual field rendering using daisyUI `form-control` / `label` / `input` / `select` classes
**Template pattern:**
```html
<div class="form-control">
  <label class="label" for="{{ field.id_for_label }}">
    <span class="label-text">{{ field.label }}</span>
  </label>
  {{ field }}
</div>
```
**Notes:** This requires updating each form template individually — a per-session task, not a global change

### Buttons

**Current:** Custom dark-theme buttons with manual hover inversion
**Proposed:** daisyUI `btn` variants

| Variant | Use |
|---|---|
| `btn btn-primary` | Primary action (Save, Submit) |
| `btn btn-ghost` | Secondary / cancel |
| `btn btn-error` | Destructive actions |
| `btn btn-sm` | Compact contexts (table row actions) |
| `btn btn-square btn-ghost` | Icon-only buttons |

### Modals

**Current:** Hand-rolled overlay (fixed backdrop + centered content via CSS Grid `place-items: center`)
**Proposed:** daisyUI `modal` + Alpine `x-show` for open/close state; focus trap via Alpine's `trap` plugin
**Current modals to migrate:** KPP upload, linguist assignment, submission confirmation (editor)

### Context menus

**Current:** Absolutely-positioned `<div>` shown/hidden via JS class toggle (right-click on segment ID, right-click on file rows)
**Proposed:** Alpine.js `x-data` + `x-show` + `@click.outside` for open/close; Tailwind-styled dropdown panel
**Notes:** Keep right-click trigger behavior in editor; project page context menu can become a hover/click row action button

### Toast notifications

**Current:** Fixed-position `<div>` with `fadeIn` CSS animation, manually constructed in JS
**Proposed:** daisyUI `toast` + `alert` components; Alpine `x-data` with auto-dismiss timer

### Segment table (editor)

**Current:** `<table>` rows grouped by translation unit, contenteditable `<td>` for target, status column as `<td class="status">`, alternating colors
**Proposed:** Keep table structure; replace manual CSS with Tailwind utilities; status column uses daisyUI `badge` with semantic token colors (see §5)
**Critical:** All JS behavior in `editor.js` is preserved as-is. Only HTML structure and CSS classes change.

### TM / Comments sidebars (editor)

**Current:** Right-side panels toggled by icon click; custom CSS for open/closed states
**Proposed:** Alpine `x-data` `{ tmOpen: true, commentsOpen: false }` for sidebar state; Tailwind transitions (`transition-all duration-200`)

### Status badges

**Current:** CSS class names used as styling hooks (`class="translated"`, etc.)
**Proposed:** daisyUI `badge` with Tailwind semantic color classes per §5

### Search / filter forms

**Current:** `main.js` (5 lines) toggles a search form visible/hidden on projects and TM list pages
**Proposed:** Alpine `x-show` replaces `main.js` entirely — no JS file needed for this

### Theme toggle

**Current:** ~~None — dark only~~ ✅ Implemented in S2
**Implementation:** daisyUI `data-theme` attribute on `<html>`, toggled via checkbox `onchange` handler. Theme choice persisted to `localStorage`; inline `<script>` in `<head>` reads it before render to prevent flash. Two custom themes: `kaplan-light` (default) and `kaplan-dark`.

---

## 7. Recommended Tech Stack

### Core stack

| Library | Version | Delivery | Purpose |
|---|---|---|---|
| **Tailwind CSS** | v4 | npm (django-tailwind) | Utility-first styling, dark mode, responsive |
| **Alpine.js** | v3 | CDN | Lightweight reactivity (toggles, dropdowns, modals) |
| **daisyUI** | v5 | npm (Tailwind plugin) | Semantic component layer (buttons, forms, modals, badges) |
| **Heroicons** | v2 | SVG sprite / inline | Replaces Material Icons |
| **Inter** | latest | CDN (Google Fonts) | Replaces Ubuntu |

> **Tailwind v4 + daisyUI v5 note:** Tailwind v4 no longer uses `tailwind.config.js`. All configuration, including the daisyUI plugin, is declared directly in the CSS file. The correct setup is:
> ```css
> @import "tailwindcss";
> @plugin "daisyui";
> ```
> `django-tailwind` now defaults to Tailwind v4, so this works out of the box.

### Optional / selective

| Library | Use case |
|---|---|
| **HTMX** | Server-driven partial updates (project list filtering, pagination). Not for the editor. |
| **Alpine Trap plugin** | Focus trap in modals |

### What stays

- `editor.js` — all business logic preserved (contenteditable, TM fetch, propagation, keyboard shortcuts, submission)
- `project.js` — checkbox, file operation logic preserved; only DOM class references updated
- `newproject.js` — dynamic TM dropdown logic preserved

### What is replaced

| Current | Replacement |
|---|---|
| `main.css` | Tailwind utilities + daisyUI |
| `editor.css` | Tailwind utilities (editor layout) |
| `main.js` | Alpine `x-show` in template |
| Material Icons | Heroicons SVG sprites |
| Ubuntu font | Inter via CDN |
| `form.as_table` | Manual daisyUI form-control markup |

### Build tooling

Use [`django-tailwind`](https://github.com/timonweb/django-tailwind) for:
- CSS purging (only include used Tailwind classes in production)
- Hot reload in development (`python manage.py tailwind start`)
- Integrates cleanly with existing `python manage.py` workflow

**Development commands (post-setup):**
```bash
python manage.py tailwind install   # npm install in theme app
python manage.py tailwind start     # watch + hot reload
python manage.py tailwind build     # production CSS
```

### CDN prototype path (optional first step)

Before adding `django-tailwind`, it is valid to prototype with Tailwind's Play CDN and Alpine via CDN tags in `base.html`. This allows visual validation without a build step. Switch to the npm build before any production deployment.

```html
<!-- Prototype only — not for production -->
<script src="https://cdn.tailwindcss.com"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js"></script>
```

---

## 8. Accessibility Goals

### WCAG AA compliance

All color combinations must meet **WCAG 2.1 AA** contrast ratio (4.5:1 for normal text, 3:1 for large text / UI components).

Key combinations to verify:
- `text-primary` on `bg-base` (both themes)
- `text-secondary` on `bg-surface` (both themes)
- Segment status badge text on badge background (both themes)
- Primary button text on `primary` background

### Keyboard navigation

The editor is already keyboard-first (Tab, Ctrl+Enter, F3, Ctrl+Insert, Ctrl+L). These shortcuts must be preserved exactly. Additions:
- All modals must be keyboard-closeable (Escape key) — Alpine Trap plugin handles this
- Dropdown menus navigable with arrow keys (Alpine `x-on:keydown`)
- Focus ring visible in both themes (`focus-visible:ring-2 focus-visible:ring-teal-500`)

### ARIA

Current templates have minimal ARIA. Add:
- `aria-label` on all icon-only buttons
- `role="dialog"` + `aria-modal="true"` on modals
- `aria-current="page"` on active nav item
- `aria-live="polite"` on toast notification region
- `aria-label` on sidebar toggle

### Screen readers

- Semantic HTML throughout (`<nav>`, `<main>`, `<aside>`, `<header>`, `<section>`)
- Table headers (`<th scope="col">`) on all data tables
- Form `<label>` associations maintained when migrating away from `form.as_table`

---

## 9. Session Roadmap

| Session | Scope | Key deliverables |
|---|---|---|
| **S1** ✅ | Research + design doc | `.design/ui-overhaul.md` committed |
| **S2** ✅ | Shell + navigation | `django-tailwind` set up; `base.html` + `index.html` reskinned; sidebar nav; header; theme toggle (light/dark); Inter + Heroicons; `main.css` removed |
| **S3** ✅ | Project management screens | `projects.html`, `project.html`, `newproject.html`; daisyUI tables; form-control markup; modals reskinned; `_apply_daisy_classes()` for forms |
| **S4** | TM + auth screens | `translation-memories.html`, `tm.html`, `newtm.html`, `tm-import.html`; auth templates |
| **S5** | Editor reskin | `editor.html` + `editor.css` replaced; JS logic preserved; segment table; TM/comments sidebars; status badges; filter bar |
| **S6** | Polish + report | `report.html`; accessibility audit; tablet layout pass; visual consistency review |

### Session 2 entry checklist

All items confirmed during Session 1 design review:

- [x] This design document reviewed and approved
- [x] Color tokens finalized — teal-600 primary, yellow draft, emerald reviewed (driven by logo color #f84000)
- [x] Font confirmed — Inter
- [x] Icon set confirmed — Heroicons
- [x] Component library confirmed — **daisyUI** (MIT licensed; Tailwind UI rejected due to per-person licensing incompatibility with open contributor model)
- [x] `django-tailwind` confirmed as dev dependency

---

## 10. Session Log

### S2 — Shell + navigation (2026-03-22/23)

**Completed:**
- django-tailwind set up with Tailwind v4 + daisyUI v5
- Custom `kaplan-light` and `kaplan-dark` themes in `theme/static_src/src/styles.css`
- `base.html` rewritten: Inter font, Alpine.js CDN, compiled CSS, Heroicons (removed Material Icons + Ubuntu)
- `index.html` rewritten: daisyUI drawer sidebar, sticky navbar, user dropdown, dark mode toggle
- Segment status CSS custom properties pre-built for S5 editor work
- Compiled CSS committed (54KB purged vs 3MB CDN)

**Findings:**
- **`main.css` global selectors** (`body`, `button`, `nav a`, `:disabled`) override daisyUI components. Scoping individual rules (`nav a` → `header nav a`) is whack-a-mole. CSS `@layer legacy` wrapping was attempted but **does not work** because Tailwind v4 itself outputs layered CSS — two layered stylesheets don't get the expected priority ordering. **Resolution:** removed `main.css` entirely; un-migrated pages will be unstyled until S3/S4 migration.
- **daisyUI `theme-controller` class** only styles the toggle visually — it does **not** include JS to switch `data-theme` on `<html>`. daisyUI is pure CSS. Theme switching requires: (1) `data-theme="kaplan-light"` on `<html>`, (2) an inline `<script>` in `<head>` to read `localStorage` before paint (prevents flash), (3) `onchange` handler on the checkbox to set `data-theme` and persist to `localStorage`.
- **`django-tailwind` build** requires `npm install` in `theme/static_src/` before first build. Running `manage.py tailwind build` from the wrong working directory fails silently with a misleading error.
- **Design doc location:** moved from `docs/` to `.design/` — `docs/` is reserved for user-facing documentation.

### S3 — Project management screens (2026-04-18)

**Completed:**
- `projects.html` reskinned: daisyUI table, Alpine `x-show` search filter (replaces `main.js` toggle), navbar breadcrumb + Create button, project count
- `project.html` reskinned: daisyUI file/reference tables, modal overlays for assign-linguist and KPP upload, styled context menu, report toast, breadcrumb navigation
- `newproject.html` reskinned: manual form-control layout replacing `form.as_table`, file input and checkbox detection, help text as title tooltips
- `forms.py`: added `_apply_daisy_classes()` utility that auto-applies daisyUI widget CSS (`input`, `select`, `file-input`, `checkbox`, `textarea`) to all form widgets via `__init__`; applied to all form classes including `SegmentCommentForm` (pre-work for S5)
- Compiled CSS rebuilt via `manage.py tailwind build`

**Findings:**
- **`getCSRFToken()` broken by S2 layout** — `project.js` grabbed the last `<input>` on the page, which was now the sidebar theme toggle checkbox (`value="kaplan-dark"`) instead of the CSRF token. `editor.js` had the same issue with the first input (sidebar drawer toggle). **Resolution:** both now use `querySelector('[name=csrfmiddlewaretoken]')`.
- **`className = "show"` strips Tailwind classes** — `project.js` and `main.js` used `el.className = "show"` to show modals/forms, which replaced all existing classes. **Resolution:** changed to `classList.add('show')` in all three JS files.
- **`#checkbox-main` class collision** — adding daisyUI's `checkbox` class to the master checkbox caused `getElementsByClassName('checkbox')` to include it alongside file checkboxes, pushing an empty UUID into selection lists. **Resolution:** removed `checkbox` class from `#checkbox-main`.
- **Assign-linguist modal `children[0]`** — wrapping the form in a modal box `<div>` broke `getElementById('assign-linguist-form').children[0]` (expected `<form>`, got `<div>`). **Resolution:** made `<form>` the direct child of the overlay.
- **Pre-existing bug: `Project.get_manifest()`** — referenced `self.source_language.iso` (non-existent attribute) instead of `.iso_code`. Same in the export view where `LanguageProfile` objects were passed to `Path()` instead of their `.iso_code` strings. Export had never worked. **Resolution:** fixed both to use `.iso_code`.

**Audit of unmigrated templates (S4–S6 scope):**
- TM templates (`translation-memories.html`, `tm.html`, `newtm.html`, `tm-import.html`): old `<header><nav>`, Material Icons, `oddrow`/`evenrow` classes, `form.as_table` — all expected to be fixed in S4
- Auth templates (login, register, change-password): extend `base.html` with `{% block body %}`, rely on removed `main.css` grid layout — S4 scope
- `editor.html`: standalone HTML, loads removed `main.css`, Material Icons, `oddrow`/`evenrow` — S5 scope
- `report.html`: standalone HTML, no styling — S6 scope

---
name: SchemesSG
description: Civic wayfinding for Singapore's assistance schemes. The Public Library Reading Room.
colors:
  schemes-bg: "#fafafa"
  schemes-surface: "#ffffff"
  schemes-ink: "#1a1a1a"
  schemes-ink-soft: "#444441"
  schemes-muted: "#5f5e5a"
  schemes-muted-light: "#b4b2a9"
  schemes-border: "#e4edf7"
  schemes-border-neutral: "#e5e7eb"
  schemes-blue-50: "#e6f1fb"
  schemes-blue-100: "#b5d4f4"
  schemes-blue-400: "#378add"
  schemes-blue-600: "#175ea6"
  schemes-blue-800: "#0c447c"
  schemes-blue-900: "#042c53"
  schemes-amber-100: "#f1cf82"
  schemes-amber-400: "#facc15"
  schemes-status-info-bg: "#f3f8fd"
  schemes-status-info-border: "#b5d4f4"
  schemes-status-info-text: "#0c447c"
  schemes-status-alert-bg: "#fff8df"
  schemes-status-alert-border: "#f1cf82"
  schemes-status-alert-text: "#604108"
typography:
  display:
    fontFamily: "Lexend, system-ui, sans-serif"
    fontSize: "clamp(2rem, 4.5vw, 3rem)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Lexend, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.005em"
  title:
    fontFamily: "Lexend, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "normal"
  body:
    fontFamily: '"Open Sans", system-ui, sans-serif'
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "normal"
  label:
    fontFamily: '"Open Sans", system-ui, sans-serif'
    fontSize: "0.6875rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.02em"
rounded:
  sm: "0.125rem"
  md: "0.375rem"
  lg: "0.625rem"
  xl: "0.75rem"
  full: "9999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2rem"
  nav: "70px"
components:
  button-solid-blue:
    backgroundColor: "{colors.schemes-blue-600}"
    textColor: "{colors.schemes-surface}"
    rounded: "{rounded.lg}"
    minHeight: "2.75rem"
    padding: "0.625rem 1rem"
  button-solid-blue-hover:
    backgroundColor: "{colors.schemes-blue-800}"
    textColor: "{colors.schemes-surface}"
  button-solid-amber:
    backgroundColor: "{colors.schemes-amber-400}"
    textColor: "{colors.schemes-ink}"
    rounded: "{rounded.lg}"
    minHeight: "2.75rem"
    padding: "0.625rem 1rem"
  button-outline-blue:
    backgroundColor: "{colors.schemes-surface}"
    textColor: "{colors.schemes-blue-600}"
    rounded: "{rounded.lg}"
    minHeight: "2.75rem"
    padding: "0.625rem 1rem"
  card-scheme:
    backgroundColor: "{colors.schemes-surface}"
    textColor: "{colors.schemes-ink}"
    rounded: "{rounded.lg}"
    padding: "1rem"
  card-scheme-hover:
    backgroundColor: "{colors.schemes-blue-50}"
  chip-category:
    rounded: "{rounded.full}"
    padding: "0.125rem 0.5rem"
  input-search:
    backgroundColor: "{colors.schemes-surface}"
    textColor: "{colors.schemes-ink}"
    rounded: "{rounded.lg}"
    padding: "0.625rem 1rem"
  status-info:
    backgroundColor: "{colors.schemes-status-info-bg}"
    textColor: "{colors.schemes-status-info-text}"
    rounded: "{rounded.lg}"
    padding: "0.75rem 1rem"
  status-alert:
    backgroundColor: "{colors.schemes-status-alert-bg}"
    textColor: "{colors.schemes-status-alert-text}"
    rounded: "{rounded.lg}"
    padding: "0.75rem 1rem"
---

# Design System: SchemesSG

## 1. Overview

**Creative North Star: "The Public Library Reading Room"**

SchemesSG is a civic wayfinding tool, and the visual system reflects that. A reading room is calm, generously spaced, and confident in its typography. It uses color the way good signage does: as quiet wayfinding, not decoration. Books are not selling themselves; the room respects the visitor's time and intelligence. The interface treats people the same way: searching for help is a normal, competent act, and the room around that act is unhurried and clear.

The system is content-led. UI chrome recedes so that scheme names, eligibility, and next steps carry every page. Color appears mostly through the category palette, which functions like archive tags or shelf labels: a Financial scheme and a Healthcare scheme are distinguishable at a glance, and that's the entire job color is doing in the catalog. Typography does the heavy lifting through scale and weight contrast, not decoration. Motion is gentle and brief: 0.4s fades, easeOut, no theatrics.

This system explicitly rejects the gov.sg starchy template (navy-on-white officialese, dense policy paragraphs, mandatory-looking forms) and the charity sympathy aesthetic (stock-photo grief, donation-CTA framing, pity hierarchy). It also rejects the SaaS hype reflex (neon gradients, glassmorphism, hero-metric templates, decorative "AI" shimmer). What's left is the room itself: warm off-white surfaces, confident headings, blue and amber used sparingly for wayfinding and emphasis, and content that earns the page.

**Key Characteristics:**
- Warm off-white background (`#fafafa`), pure white surfaces for cards and inputs
- Lexend for headings, Open Sans for body — confident hierarchy, comfortable reading
- Blue-600 as the single working accent; the category palette as wayfinding
- Pill-rounded category chips, 10px radius cards, full borders over side stripes
- Flat-by-default; shadows used sparingly and only on hover or focus
- Motion: 0.4s, easeOut, decorative only, never required; every persistent animation has a static reduced-motion equivalent

## 2. Colors

A warm-neutral catalog with one civic-blue accent and a 10-category wayfinding palette. Color is signage, not decoration.

### Primary
- **Civic Blue** (`#175ea6`, `--schemes-blue-600`): The single working accent. Used on primary buttons, focused inputs, link text, and the small left-edge marker on `SchemeCard` hover. Appears in the deeper `--schemes-blue-800` (`#0c447c`) for hover states and `--schemes-blue-900` (`#042c53`) for emphasis ink in headings on key surfaces.
- **Civic Blue Tint** (`#e6f1fb`, `--schemes-blue-50`): The card hover surface and the only large blue field in the catalog. Light enough to read black text on, distinct enough to register state change.

### Secondary
- **Amber** (`#facc15`, `--schemes-amber-400`): Reserved for alerts, advisories, and rare strong CTAs that need deliberate emphasis, such as submitting a form or starting a new flow. Never decorative. The lighter `--schemes-amber-100` (`#f1cf82`) carries alert borders and amber hover states.

### Tertiary: The Category Palette
Ten semantic categories, each defined as a `bg / border / text` triplet:
`Financial Assistance`, `Family & Children`, `Health & Wellbeing`, `Housing & Food`, `Education`, `Employment & Training`, `Seniors & Caregiving`, `Disability & Transport`, `Legal & Safety`, and `Community Support`. Applied via the `getSchemeCategoryChipClassName()` utility on `<CategoryTag>` and `<Tag>`. Specific backend scheme types retain their original labels while borrowing the mapped category color. These are wayfinding labels, not brand colors. They never appear as page backgrounds, gradients, or large fields.

### Neutral
- **Page Background** (`#fafafa`, `--schemes-bg`): Warm off-white. The page itself.
- **Surface** (`#ffffff`, `--schemes-surface`): Cards, inputs, popovers, elevated surfaces.
- **Ink** (`#1a1a1a`, `--schemes-ink`): Primary text. Near-black, slightly warm.
- **Ink Soft** (`#444441`, `--schemes-ink-soft`): Body paragraphs, scheme descriptions.
- **Muted** (`#5f5e5a`, `--schemes-muted`): Secondary metadata, captions, placeholders.
- **Muted Light** (`#b4b2a9`, `--schemes-muted-light`): Tertiary text, dividers in copy.
- **Border** (`#e4edf7`, `--schemes-border`): Card and input borders. A faint blue-tinted neutral.
- **Neutral Border** (`#e5e7eb`, `--schemes-border-neutral`): Subdivisions inside cards, list separators.

### Named Rules

**The Wayfinding Rule.** Color carries meaning or it doesn't appear. Civic Blue means "default primary action / link / focus." The category palette means "what kind of help this is." Amber means "pay attention" and is limited to alerts or rare strong CTAs. Anything else is neutral. No decorative color, anywhere.

**The One Accent Rule.** Civic Blue (`--schemes-blue-600`) is the default working accent on product surfaces. It carries primary buttons, link text, focus rings, and interactive markers. It should occupy ≤10% of any product screen at rest. Amber is an exception for alerts and rare strong CTAs; category chips remain wayfinding rather than general accent.

**The Hex-Now, OKLCH-Later Rule.** The codebase currently keeps both `--schemes-*` hex tokens and a parallel OKLCH semantic layer (`--primary`, `--background`, etc.) for HeroUI v3 compatibility. The hex tokens are canonical for product surfaces today. Migration to OKLCH-only is a known in-flight effort, not a license to introduce hex/OKLCH duplicates in new code. New tokens land in OKLCH.

## 3. Typography

**Display Font:** Lexend (with system-ui, sans-serif fallback)
**Body Font:** Open Sans (with system-ui, sans-serif fallback)
**Label Font:** Open Sans (uppercase or weighted variants for labels)

**Character:** Lexend is engineered for reading proficiency: open shapes, generous spacing, calm authority without warmth-loss. Open Sans is the steady civic body face. Together they read as competent and human, not corporate, not formal. The pairing is intentional civic-tech, not consumer-tech, and not gov.sg.

### Hierarchy

- **Display** (Lexend, 600, `clamp(2rem, 4.5vw, 3rem)`, line-height 1.1): Hero headlines on `/about` and the agentic landing surface. Used sparingly. Never on app-shell screens.
- **Headline** (Lexend, 600, 1.5rem, line-height 1.2): Section titles inside the product (scheme detail page title, results header).
- **Title** (Lexend, 600, 1.125rem, line-height 1.3): Card titles, scheme names in result lists, dialog titles.
- **Body** (Open Sans, 400, 1rem, line-height 1.55, max width 65–75ch): Scheme descriptions, eligibility paragraphs, agent output. Always capped at a comfortable measure; never full-bleed prose on wide screens.
- **Label** (Open Sans, 600, 0.6875rem, letter-spacing 0.02em): Category chip text, table headers, small metadata. Tracked slightly to read clearly at small sizes.

### Named Rules

**The Reading-Measure Rule.** Body copy is capped at 65–75ch. Scheme descriptions and AI agent output both. A 1200px-wide paragraph is not "more information"; it is a wall. The eye gives up before the user does.

**The Lexend-For-Heads Rule.** Lexend appears on headings only. Body copy is Open Sans. Don't reach for Lexend at small sizes — its shapes are tuned for scale, and below 18px it loses the calm it brings at 24px and up.

## 4. Elevation

The system is flat by default. Surfaces sit on the warm-neutral background without shadows. Depth, when needed, comes from tonal layering (`--schemes-bg` → `--schemes-surface` → `--schemes-blue-50` on hover) and from full borders, never from drop shadows at rest.

Shadows appear only as a response to state. The `SchemeCard` lifts on hover with a soft, blue-tinted glow (`0 2px 12px rgba(24, 95, 165, 0.1)`); inputs gain a faint `shadow-sm` on focus inside the chat hero. Beyond those, shadows are absent.

### Shadow Vocabulary

- **Card Hover Glow** (`box-shadow: 0 2px 12px rgba(24, 95, 165, 0.1)`): Used on `SchemeCard:hover`. The blue tint connects the lift to the wayfinding palette without introducing a new color.
- **Input Focus Lift** (`shadow-sm` from Tailwind, ~`0 1px 2px 0 rgb(0 0 0 / 0.05)`): On the chat landing input and primary search field at rest, removed on submit.

### Named Rules

**The Flat-By-Default Rule.** Cards, popovers, and modals are flat at rest. A card with a drop shadow doing nothing is decoration, not affordance. Shadows only appear in response to hover, focus, or floating-state (popovers, dropdowns).

**The No-Glass Rule.** Backdrop-filter blurs and translucent surfaces are forbidden in this product. The reading room is not a nightclub. Every surface is opaque, every border is full-width, every edge is honest about what it is.

## 5. Components

### Buttons
- **Shape:** Rounded rectangle, 10px radius (`{rounded.lg}` = `0.625rem`).
- **Solid Blue:** `productButtonSolidBlue`. `bg --schemes-blue-600`, `text white`. Hover: `bg --schemes-blue-800`. The default primary action.
- **Solid Amber:** `productButtonSolidAmber`. `bg --schemes-amber-400`, `text --schemes-ink`. Used only for alerts or rare strong CTAs, including form submission and deliberate flow entry.
- **Outline Blue:** `productButtonOutlineBlue`. White surface, blue border and text. The standard secondary action.
- **Outline Neutral:** `productButtonOutlineNeutral`. White surface, neutral border and ink. Used for cancel, clear, and low-emphasis utility actions.
- **Focus:** Visible 2px ring in `--schemes-blue-400`, offset 2px. Always present, never `outline: none`.
- **Touch Target:** Every interactive button and icon control is at least 44px high and wide on mobile.
- **Sizes:** `productButtonCompact` (44px), `productButtonDefault` (minimum 44px), and `productButtonProminent` (minimum 48px). Names describe hierarchy and use, not arbitrary small/medium/large tiers.
- **Responsive Labels:** Dense toolbars may use an icon-only control on mobile and reveal its text label from `sm` upward. Icon-only controls require an accessible name.

### Motion and Loading
- **Default:** State transitions run for 150–200ms; entrances may run for about 400ms. Use easeOut and avoid spring, bounce, or elastic behavior on product surfaces.
- **Loading Status:** A restrained moving highlight may be used only on short status text while work is active. It is functional feedback, not decorative headline treatment.
- **Reduced Motion:** The Lottie chat spinner becomes the static SchemesSG logo; shiny status text becomes solid blue text; rotating status words render statically; the schemes-tab pulse becomes a fixed blue notification marker.
- **State Independence:** Motion may attract attention but cannot be the sole carrier of loading, completion, or notification state.

### Chips: Category Tags
- **Style:** Pill (`{rounded.full}`), tight padding (`0.125rem 0.5rem` for `CategoryTag`, `0.125rem 0.625rem` for the larger detail-page `Tag`).
- **Color:** Triplet tokens per category — `bg`, `border`, `text` from the `--schemes-category-{name}-*` family. Resolved via `getSchemeCategoryChipClassName()`.
- **Typography:** `text-[10px]` (CategoryTag) or `text-[11px]` (Tag), `font-semibold`, no uppercase. Reads as a quiet label, not a shouting badge.
- **State:** Single-state. Categories don't toggle on the chip itself; selection lives in the filter UI.

### Cards: SchemeCard
- **Corner Style:** 10px radius (`{rounded.lg}`).
- **Background:** `--schemes-surface` at rest, `--schemes-blue-50` on hover.
- **Shadow Strategy:** Flat at rest. On hover: lift `-translate-y-0.5` plus the Card Hover Glow (`0 2px 12px rgba(24, 95, 165, 0.1)`). Transition 150–200ms, easeOut.
- **Border:** Full 1px border in `--schemes-border` on all four sides. Never a left-edge stripe.
- **Internal Padding:** `p-4` (1rem). Card content uses `gap-2` between elements for the default tight rhythm.
- **Anatomy:** Title (Title role, Lexend 600 1.125rem), description (Body, capped to 2-3 lines), category chip row at the bottom.

### Inputs / Fields
- **Style:** White surface, 10px radius, full 1px border in `--schemes-border`, padding `0.625rem 1rem`.
- **Focus:** Border shifts to `--schemes-blue-400`, plus a 2px focus ring in the same color at 30% opacity. No glow, no animation longer than 150ms.
- **Placeholder:** `--schemes-muted`. Always sentence-case; never uppercase or italic.
- **Error:** Border `--schemes-status-alert-border`, helper text in `--schemes-status-alert-text`. Helper text appears below the field, never as a tooltip on hover.

### Navigation
- **Style:** Top nav, `--spacing-nav` height (70px). White surface, full bottom border in `--schemes-border-neutral`.
- **Typography:** Body face (Open Sans), 14px, weight 500.
- **States:** Default `--schemes-ink-soft`, hover `--schemes-blue-600`, active route `--schemes-blue-900` with a 2px underline in `--schemes-blue-600`.
- **Mobile:** Disclosed sheet, full-height, same color rules. No off-canvas drawer with translucent overlay.

### Status Banners
- **Info:** `bg --schemes-status-info-bg`, border `--schemes-status-info-border`, text `--schemes-status-info-text`. 10px radius, full border. Used for non-blocking guidance.
- **Alert:** `bg --schemes-status-alert-bg`, border `--schemes-status-alert-border`, text `--schemes-status-alert-text`. Used for advisories and known issues.
- **Both** sit inline in content flow. Banners are not modals. They never dismiss themselves and never animate in.

### Signature Component: BulletItem
A custom list item with a 6px dot in `--schemes-muted`, `gap-2.5` between dot and text, body-size copy. Used in scheme detail pages for eligibility lists, supporting documents, next-step lists. It replaces native `<ul>` markers because the library-tag aesthetic prefers a single calm dot to a bullet glyph that varies across browsers and fonts.

## 6. Do's and Don'ts

### Do:
- **Do** lead with content. Scheme names, eligibility, and next steps carry the page; UI chrome recedes.
- **Do** use Civic Blue (`--schemes-blue-600`) as the single working accent on product screens. ≤10% of the screen at rest.
- **Do** use the category palette as wayfinding, like archive tags. Bg + border + text triplets only.
- **Do** cap body copy at 65–75ch. Both in scheme descriptions and in agent output.
- **Do** keep cards flat at rest. Lift them on hover with the Card Hover Glow and a `-translate-y-0.5`.
- **Do** use full 1px borders in `--schemes-border`. Same on all four sides.
- **Do** use Lexend for headings and Open Sans for body. Don't reach for Lexend below 18px.
- **Do** respect `prefers-reduced-motion`. Motion is always decorative, never required to convey state.
- **Do** provide explicit static equivalents for persistent loading and notification animations.
- **Do** maintain a minimum 44px mobile target for buttons, links styled as buttons, icon actions, tabs, and compact filters.
- **Do** keep transitions at 150–200ms (state) and 400ms (entrance), easeOut.

### Don't:
- **Don't** use the gov.sg starchy template. No navy-and-white officialese, no dense policy paragraphs, no mandatory-looking forms.
- **Don't** use the charity sympathy aesthetic. No stock photos of grief, no donation-CTA framing, no pity hierarchy. We are a wayfinding tool, not a fundraiser.
- **Don't** reach for SaaS hype: no neon gradients, glassmorphism, hero-metric templates, or decorative shimmer. A restrained status-text highlight is allowed only while communicating active work.
- **Don't** ship identical icon-heading-text card grids. The library is not a SaaS pricing page.
- **Don't** use `border-left` greater than 1px as a colored accent stripe on cards or callouts. Use a full border or a background tint instead.
- **Don't** apply gradient text via `background-clip: text`. Solid color, weight contrast.
- **Don't** introduce new hex tokens parallel to the existing OKLCH layer. New tokens land in OKLCH; the hex layer is being migrated, not extended.
- **Don't** use Lexend at body sizes or Open Sans at display sizes. Each face has its job.
- **Don't** add drop shadows to cards or modals at rest. Flat-by-default; shadows only on hover or focus.
- **Don't** use `bounce` or `elastic` easing. EaseOut, easeInOut, or none.
- **Don't** use em dashes in UI copy. Commas, colons, semicolons, parentheses.
- **Don't** refer to users as "beneficiaries", "those in need", "applicants", or any institutional euphemism. Plain language; treat people as people.

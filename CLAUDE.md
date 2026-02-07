# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pnpm dev          # Start dev server (Vite, port 5173)
pnpm build        # TypeScript check + production build
pnpm lint         # ESLint (flat config)
pnpm preview      # Preview production build
```

## Architecture

Single-page landing site for Schemes.sg — an AI-powered search engine for social assistance schemes in Singapore. Built with React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui, and motion (framer-motion successor).

### Component Organization

- **`src/components/layout/`** — Persistent chrome: `Navbar` (sticky, blur-on-scroll, mobile hamburger) and `Footer`
- **`src/components/sections/`** — Full-width page sections rendered sequentially in `App.tsx`: Hero → Features → HowItWorks → Stats → Testimonial → FAQ → CTA
- **`src/components/shared/`** — Reusable building blocks: `SectionWrapper` (consistent padding + max-w-7xl container), `ScrollingColumn` (infinite vertical text marquee), `ScrollingLogoColumn` (infinite vertical logo marquee), `AnimatedCounter` (number count-up on scroll)
- **`src/components/ui/`** — shadcn/ui primitives (button, card, badge, accordion, separator). Add new ones via `pnpm dlx shadcn@latest add <component>`

### Data Layer

All content is centralized in `src/data/`:
- **`content.ts`** — Every text string on the page (hero copy, features, FAQ answers, nav links, footer links, stats). Single source of truth for copy changes.
- **`agencies.ts`** — 12 curated Singapore agencies with `name`, `shortName`, and `logo` URL (hosted on Sirv CDN). Sourced from production Firestore export.

### Styling

- **Tailwind CSS v4** via Vite plugin — no `tailwind.config.js`, theme is defined in `@theme inline` block in `src/index.css`
- **Color system**: OKLch-based. Primary = emerald green palette, neutrals = warm stone tones. CSS variables set in `:root` for shadcn compatibility.
- **Fonts**: Plus Jakarta Sans Variable (body/`--font-sans`) + DM Serif Display (headlines/`--font-serif`), imported via `@fontsource` in `main.tsx`
- **Custom CSS**: `.animate-float` keyframe for hero icon, `.grain-overlay` subtle texture
- Use `cn()` from `@/lib/utils` for conditional class merging (clsx + tailwind-merge)

### Animation Pattern

All scroll-triggered animations use motion/react:
```tsx
<motion.div
  initial={{ opacity: 0, y: 30 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true, margin: "-80px" }}
  transition={{ duration: 0.5, delay: index * 0.1 }}
/>
```
Scrolling columns and AnimatedCounter respect `useReducedMotion()` for accessibility.

### Path Aliases

`@/` maps to `src/` — configured in both `vite.config.ts` and `tsconfig.app.json`.

### TypeScript

Strict mode with `noUnusedLocals` and `noUnusedParameters` enabled. Fontsource imports require `@ts-expect-error` comments due to missing type declarations.

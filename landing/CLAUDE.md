# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pnpm dev          # Start dev server (Vite, port 5173)
pnpm build        # TypeScript check + production build
pnpm lint         # ESLint (flat config)
pnpm preview      # Preview production build
```

## Deployment

Firebase Hosting multi-site deployment to project `schemessg-v3-dev`:

```bash
pnpm build && firebase deploy --only hosting:schemes-landing-dev
```

Live URL: https://schemes-landing-dev.web.app

## Architecture

Single-page landing site for Schemes.sg -- an AI-powered search engine for social assistance schemes in Singapore. Built with React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui, and motion (framer-motion successor).

### Component Organization

- **`src/components/layout/`** -- Persistent chrome: `Navbar` (sticky, blur-on-scroll, mobile hamburger, language toggle) and `Footer`
- **`src/components/sections/`** -- Full-width page sections lazy-loaded in `App.tsx`: Hero -> Featured -> Features -> Agencies -> Testimonial -> FAQ -> CTA
- **`src/components/shared/`** -- Reusable building blocks: `SectionWrapper` (consistent padding + max-w-7xl container), `ScrollingColumn` (infinite vertical text marquee), `ScrollingLogoColumn` (infinite vertical logo marquee), `AnimatedCounter` (number count-up on scroll), `LanguageToggle` (EN/中文 pill toggle), `SectionSkeleton` (shimmer loading skeletons)
- **`src/components/ui/`** -- shadcn/ui primitives (button, card, badge, accordion, separator). Add new ones via `pnpm dlx shadcn@latest add <component>`

### i18n (Internationalization)

Lightweight React Context-based i18n supporting English and Simplified Chinese (extensible to Malay/Tamil):
- **`src/i18n/types.ts`** -- `Locale` type + `Translations` interface (typed for autocompletion)
- **`src/i18n/translations/en.ts`** / **`zh.ts`** -- All user-facing strings (~90 keys)
- **`src/i18n/LanguageContext.tsx`** -- `LanguageProvider` + `useLanguage()` hook returning `{ locale, setLocale, t }`
- Language preference persisted in `localStorage("schemes-lang")`, defaults to English
- Agency names, logos, and decorative illustration text stay in English for both languages

### Data Layer

- **`src/data/agencies.ts`** -- 12 curated Singapore agencies with `name`, `shortName`, and `logo` URL. Sourced from production Firestore export.

### Styling

- **Tailwind CSS v4** via Vite plugin -- no `tailwind.config.js`, theme is defined in `@theme inline` block in `src/index.css`
- **Color system**: OKLch-based. Amber/warm accent palette (matching logo orange gradient), blue/trust palette (matching logo blue gradient), pure neutral grays. CSS variables set in `:root` for shadcn compatibility.
- **Fonts**: Plus Jakarta Sans Variable (body/`--font-sans`) + DM Serif Display (headlines/`--font-serif`), imported via `@fontsource` in `main.tsx`. CJK fallbacks: PingFang SC, Hiragino Sans GB, Microsoft YaHei.
- **Custom CSS**: `@keyframes shimmer` for skeleton loading, `.animate-float` for hero icon, `.grain-overlay` subtle texture
- Use `cn()` from `@/lib/utils` for conditional class merging (clsx + tailwind-merge)

### Skeleton Shimmer Loading

All sections are code-split with `React.lazy()` and wrapped in `<Suspense>` with shimmer skeleton fallbacks. This means each section loads independently and shows a shimmer placeholder until its chunk arrives.

**When adding a new section:**
1. Create the section component in `src/components/sections/`
2. Add a corresponding skeleton in `src/components/shared/SectionSkeleton.tsx` -- use the existing `Block` helper with `shimmerClass` for consistent shimmer styling
3. In `App.tsx`, lazy-import the section and wrap it in `<Suspense fallback={<YourSkeleton />}>`
4. The skeleton in `index.html` (pre-React load) should also be updated to include the new section's approximate shape

Pre-React skeleton HTML is also embedded in `index.html` inside `<div id="root">` for the initial page load before any JS executes. React's `createRoot().render()` replaces it automatically.

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
Scrolling columns and AnimatedCounter respect `useReducedMotion()` for accessibility. Shimmer animation respects `prefers-reduced-motion`.

### Path Aliases

`@/` maps to `src/` -- configured in both `vite.config.ts` and `tsconfig.app.json`.

### TypeScript

Strict mode with `noUnusedLocals` and `noUnusedParameters` enabled. Fontsource imports require `@ts-expect-error` comments due to missing type declarations.

# Schemes.sg Landing Site

Landing page for [Schemes.sg](https://schemes.sg) -- an AI-powered search engine that helps people in Singapore find social assistance schemes they're eligible for.

**Live:** https://schemes-landing-dev.web.app

## Tech Stack

- **React 19** + **TypeScript** (strict mode)
- **Vite 7** dev server & bundler
- **Tailwind CSS v4** (Vite plugin, no config file -- theme defined in `src/index.css`)
- **shadcn/ui** component primitives
- **motion** (framer-motion successor) for scroll-triggered animations
- **pnpm** package manager

## Getting Started

```bash
# Install dependencies
pnpm install

# Start dev server (http://localhost:5173)
pnpm dev

# Type-check + production build
pnpm build

# Lint
pnpm lint

# Preview production build
pnpm preview
```

## Project Structure

```
landing/
├── public/                  # Static assets
├── src/
│   ├── components/
│   │   ├── layout/          # Navbar, Footer
│   │   ├── sections/        # Page sections (Hero, Featured, Features, Agencies, etc.)
│   │   ├── shared/          # Reusable components (SectionWrapper, AnimatedCounter, etc.)
│   │   └── ui/              # shadcn/ui primitives (button, card, badge, accordion, separator)
│   ├── data/                # Static data (agencies, content)
│   ├── i18n/                # Internationalization (EN / 中文)
│   │   └── translations/    # Translation files
│   ├── lib/                 # Utilities (cn helper)
│   ├── App.tsx              # Root component with lazy-loaded sections
│   ├── main.tsx             # Entry point
│   └── index.css            # Tailwind theme + custom animations
├── index.html               # Shell with pre-React skeleton HTML
├── firebase.json            # Firebase Hosting config
└── vite.config.ts
```

## Page Sections

All sections are code-split via `React.lazy()` and show shimmer skeleton placeholders while loading:

1. **Hero** -- headline, search CTA, scrolling text columns
2. **Featured** -- media mentions and press
3. **Features** -- what Schemes.sg offers
4. **Agencies** -- 12 Singapore government agencies in the database
5. **Testimonial** -- user/partner quotes
6. **FAQ** -- common questions (accordion)
7. **CTA** -- final call to action

## Internationalization

Supports English and Simplified Chinese via a lightweight React Context system. Toggle is in the Navbar. Language preference is persisted to `localStorage`.

To add a new language:
1. Add the locale to `src/i18n/types.ts`
2. Create a translation file in `src/i18n/translations/`
3. Register it in `src/i18n/index.ts`

## Styling

- **Color system:** OKLch-based with amber/warm accents and blue/trust palette, matching the Schemes.sg brand
- **Fonts:** Plus Jakarta Sans Variable (body) + DM Serif Display (headlines), with CJK fallbacks
- **Path alias:** `@/` maps to `src/`
- **Utility:** use `cn()` from `@/lib/utils` for conditional class merging

## Adding a shadcn/ui Component

```bash
pnpm dlx shadcn@latest add <component>
```

## Deployment

Firebase Hosting, multi-site project `schemessg-v3-dev`:

```bash
pnpm build && firebase deploy --only hosting:schemes-landing-dev
```

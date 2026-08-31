import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    clearMocks: true,
    restoreMocks: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      reportsDirectory: ".coverage",
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        // Test infrastructure is not application runtime code.
        "src/test/**",
        // Static presentation configuration has no executable behavior.
        "src/data/landing-agencies.ts",
        "src/lib/design-system/motion.ts",
        "src/lib/design-system/product-styles.ts",
        "src/lib/landing-i18n/translations/en.ts",
        "src/lib/landing-i18n/translations/zh.ts",
        // Async and framework-owned Next.js entrypoints stay at the browser seam.
        "src/app/layout.tsx",
        "src/app/{robots,sitemap}.ts",
        "src/app/*landing*/about/layout.tsx",
        "src/app/*landing*/about/page.tsx",
        "src/app/*main*/layout.tsx",
        "src/app/*main*/page.tsx",
        "src/app/*main*/catalog/page.tsx",
        "src/app/*main*/catalog/*/page.tsx",
        "src/app/*main*/schemes/*/page.tsx",
        // Visual-only animation modules do not own product or domain state.
        "src/components/animations/blur-fade.tsx",
        "src/components/animations/magic-card.tsx",
        "src/components/animations/number-ticker.tsx",
        "src/components/animations/scroll-based-velocity.tsx",
        "src/components/animations/shiny-text.tsx",
        "src/components/animations/text-shimmer-wave.tsx",
        "src/components/animations/typing-animation.tsx",
        "src/components/animations/word-rotate.tsx",
        // Landing presentation and demos do not own product or domain state.
        "src/components/landing/about-page-content.tsx",
        "src/components/landing/sections/agencies-section.tsx",
        "src/components/landing/sections/cta-section.tsx",
        "src/components/landing/sections/faq-section.tsx",
        "src/components/landing/sections/featured-section.tsx",
        "src/components/landing/sections/features-section.tsx",
        "src/components/landing/sections/hero-section.tsx",
        "src/components/landing/sections/testimonial-section.tsx",
        "src/components/landing/shared/Marquee.tsx",
        "src/components/landing/shared/scrolling-column.tsx",
        "src/components/landing/shared/scrolling-logo-column.tsx",
        "src/components/landing/shared/section-skeleton.tsx",
        "src/components/landing/shared/section-wrapper.tsx",
        "src/components/landing/ui/badge.tsx",
        "src/components/landing/ui/button.tsx",
        "src/components/layout/footer.tsx",
        "src/components/layout/page-shell.tsx",
        "src/components/ui/card.tsx",
        "src/components/ui/typography.tsx",
        // Static placeholders have no domain/state decisions.
        "src/components/feedback/empty-state.tsx",
        "src/components/schemes/scheme-skeleton.tsx",
      ],
      thresholds: {
        statements: 70,
        branches: 60,
        functions: 70,
        lines: 70,
      },
    },
  },
});

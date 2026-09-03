import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  // Keep existing Next 16 migration findings visible without weakening these
  // rules for the rest of the frontend.
  {
    files: ["src/components/animations/text-shimmer-wave.tsx"],
    rules: {
      "react-hooks/static-components": "warn",
    },
  },
  {
    files: [
      "src/components/animations/typing-animation.tsx",
      "src/components/catalog/catalog-detail.tsx",
      "src/components/chat/chat-message-list.tsx",
      "src/components/layout/navbar.tsx",
      "src/hooks/use-hide-on-scroll.ts",
      "src/hooks/use-scheme-detail-navigation.ts",
    ],
    rules: {
      "react-hooks/set-state-in-effect": "warn",
    },
  },
  {
    files: ["src/components/chat/chat-page.tsx"],
    rules: {
      "react-hooks/immutability": "warn",
    },
  },
  {
    files: ["src/components/chat/schemes-list.tsx"],
    rules: {
      "react-hooks/refs": "warn",
    },
  },
  {
    files: [
      "src/components/layout/footer.tsx",
      "src/components/layout/navbar.tsx",
    ],
    rules: {
      "@next/next/no-html-link-for-pages": "warn",
    },
  },
  globalIgnores([
    ".coverage/**",
    ".next/**",
    "coverage/**",
    "out/**",
    "playwright-report/**",
    "test-results/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

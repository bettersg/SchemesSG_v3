import path from "node:path";
import { fileURLToPath } from "node:url";

const configDirectory = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  outputFileTracingRoot: configDirectory,

  experimental: {
    // Three first-party stylesheets blocked first paint (~1.3s of the 4.8s
    // mobile LCP on a scheme page). Inlining removes the round trip.
    inlineCss: true,
  },

  // CSP is deliberately omitted: it needs a nonce strategy for Next's inline
  // scripts and would break the app if added blind.
  // /catalog/all was the unfiltered view before /catalog became it. Permanent,
  // so any inbound link or indexed copy consolidates onto the canonical URL.
  async redirects() {
    return [
      { source: "/catalog/all", destination: "/catalog", permanent: true },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
    ];
  },

  env: {
    APP_ENV: process.env.APP_ENV || "development",
  },
  images: {
    remotePatterns: [
      {
        hostname: "schemes.sg",
      },
    ],
  },
};

export default nextConfig;

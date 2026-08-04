import path from "node:path";
import { fileURLToPath } from "node:url";

const configDirectory = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  outputFileTracingRoot: configDirectory,

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

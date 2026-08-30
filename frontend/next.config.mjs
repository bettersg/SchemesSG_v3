/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  env: {
    APP_ENV: process.env.APP_ENV || "development",
  },
  // Lets next.onFetch intercept async Server Component requests only in E2E.
  experimental: {
    testProxy:
      process.env.NEXT_PUBLIC_API_BASE_URL === "https://api.e2e.test",
  },
  images: {
    remotePatterns: [
      {
        hostname: "schemes.sg",
      },
    ],
  },
  // You can add environment-specific configurations here if needed
  // For example:
  // publicRuntimeConfig: {
  //   apiUrl: process.env.APP_ENV === 'production'
  //     ? 'https://api.example.com'
  //     : 'https://staging-api.example.com',
  // },
};

export default nextConfig;

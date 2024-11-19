/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: 'export',
  env: {
    APP_ENV: process.env.APP_ENV || 'development',
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

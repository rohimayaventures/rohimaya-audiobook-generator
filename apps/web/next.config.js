/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Environment variables exposed to the browser (must be prefixed with NEXT_PUBLIC_)
  env: {
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    NEXT_PUBLIC_ENGINE_API_URL: process.env.NEXT_PUBLIC_ENGINE_API_URL || 'http://localhost:8000',
  },

  // Output configuration for deployment
  // output: 'standalone',  // Disabled for Vercel - Vercel handles this automatically

  // Disable automatic static optimization for /app routes (needed for dynamic features)
  // experimental: {
  //   appDir: true,  // Not needed in Next.js 14, app directory is default
  // },
}

module.exports = nextConfig

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Environment variables exposed to the browser (must be prefixed with NEXT_PUBLIC_)
  env: {
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    NEXT_PUBLIC_ENGINE_API_URL: process.env.NEXT_PUBLIC_ENGINE_API_URL || 'http://localhost:8000',
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          },
        ],
      },
    ]
  },

  // Output configuration for deployment
  // output: 'standalone',  // Disabled for Vercel - Vercel handles this automatically

  // Disable automatic static optimization for /app routes (needed for dynamic features)
  // experimental: {
  //   appDir: true,  // Not needed in Next.js 14, app directory is default
  // },
}

module.exports = nextConfig

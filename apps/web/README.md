# Rohimaya Audiobook Generator - Web Frontend

## Overview

Next.js 14 web application with App Router for the AuthorFlow audiobook generation platform.

## Structure

```
apps/web/
├── app/                     # Next.js 14 App Router
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Public landing page (/)
│   └── app/                # Internal app shell (/app)
│       └── page.tsx        # Dashboard (coming soon)
├── package.json            # Dependencies
├── tsconfig.json           # TypeScript config
├── next.config.js          # Next.js config
└── .env.local              # Environment variables (NOT tracked)
```

## Getting Started

### 1. Install Dependencies

```bash
cd apps/web
npm install
```

### 2. Set Up Environment Variables

Make sure `.env.local` exists and is configured:

```bash
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_ENGINE_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

See [ENV_SETUP_GUIDE.md](../../ENV_SETUP_GUIDE.md) for complete setup instructions.

### 3. Run Development Server

```bash
npm run dev
```

Visit:
- **Landing Page:** http://localhost:3000
- **App Dashboard:** http://localhost:3000/app

### 4. Build for Production

```bash
npm run build
npm start
```

## Routes

### Public Routes
- `/` - Landing page with features and CTA buttons

### Protected Routes (Coming Soon)
- `/app` - Dashboard shell (currently a placeholder)
- `/app/jobs` - Job management (planned)
- `/app/settings` - User settings (planned)

## Features

### ✅ Implemented
- Landing page with gradient branding
- App dashboard shell with API health check
- Responsive design with inline styles
- TypeScript support
- Next.js 14 App Router

### 🚧 Planned
- User authentication (Supabase Auth)
- Job creation UI (upload manuscript)
- Voice selection and configuration
- Real-time progress tracking
- Download completed audiobooks
- Billing integration (Stripe)

## Environment Variables

Required environment variables for the frontend:

```bash
# App URLs
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_ENGINE_API_URL=http://localhost:8000

# Supabase (public keys safe for frontend)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key

# Optional: Stripe (for billing)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

See `.env.local` for complete list of optional variables.

## Deployment

### Vercel (Recommended)

1. Connect GitHub repo to Vercel
2. Set root directory: `apps/web`
3. Add environment variables in Vercel dashboard
4. Deploy

**Vercel Configuration:**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install",
  "framework": "nextjs"
}
```

### Environment Variables for Production

Add these in Vercel Dashboard → Settings → Environment Variables:
- `NEXT_PUBLIC_APP_URL` (your production domain)
- `NEXT_PUBLIC_ENGINE_API_URL` (Railway backend URL)
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- All optional vars (Stripe, Google OAuth, etc.)

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Inline styles (for now, TailwindCSS planned)
- **Auth:** Supabase Auth (planned)
- **Database:** Supabase PostgreSQL (planned)
- **Storage:** Supabase Storage (planned)
- **Billing:** Stripe (planned)
- **Deployment:** Vercel

## Scripts

```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run start      # Start production server
npm run lint       # Run ESLint
npm run type-check # TypeScript type checking
```

---
**Last Updated:** 2025-11-22
**Status:** ✅ Basic shell implemented, ready for feature development

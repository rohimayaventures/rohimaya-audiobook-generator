import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

/**
 * Next.js Middleware - AuthorFlow Studios
 *
 * Handles:
 * - Session refresh on each request
 * - Protected route enforcement
 * - Redirect logged-in users away from auth pages
 * - Session timeout check
 */

// Routes that require authentication
const protectedRoutes = [
  '/dashboard',
  '/library',
  '/settings',
  '/billing',
  '/job',
]

// Routes that should redirect to dashboard if already logged in
const authRoutes = ['/login', '/signup']

// Session timeout in milliseconds (30 minutes of inactivity)
const SESSION_TIMEOUT_MS = 30 * 60 * 1000

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          request.cookies.set({
            name,
            value,
            ...options,
          })
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          })
          response.cookies.set({
            name,
            value,
            ...options,
          })
        },
        remove(name: string, options: CookieOptions) {
          request.cookies.set({
            name,
            value: '',
            ...options,
          })
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          })
          response.cookies.set({
            name,
            value: '',
            ...options,
          })
        },
      },
    }
  )

  // Refresh session if it exists
  const { data: { session } } = await supabase.auth.getSession()

  const pathname = request.nextUrl.pathname

  // Check if the current route is protected
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route))

  // Check if the current route is an auth route (login/signup)
  const isAuthRoute = authRoutes.some(route => pathname.startsWith(route))

  // Check if user is on the homepage
  const isHomepage = pathname === '/'

  // Session timeout check
  if (session) {
    const lastActivity = request.cookies.get('af_last_activity')?.value
    const now = Date.now()

    if (lastActivity) {
      const lastActivityTime = parseInt(lastActivity, 10)
      const timeSinceActivity = now - lastActivityTime

      // If session has timed out due to inactivity, sign out
      if (timeSinceActivity > SESSION_TIMEOUT_MS) {
        // Clear session and redirect to login
        await supabase.auth.signOut()

        const redirectUrl = new URL('/login', request.url)
        redirectUrl.searchParams.set('message', 'session_expired')

        const redirectResponse = NextResponse.redirect(redirectUrl)
        redirectResponse.cookies.delete('af_last_activity')
        return redirectResponse
      }
    }

    // Update last activity time
    response.cookies.set({
      name: 'af_last_activity',
      value: now.toString(),
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24, // 24 hours
    })
  }

  // Protected route without session - redirect to login
  if (isProtectedRoute && !session) {
    const redirectUrl = new URL('/login', request.url)
    redirectUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(redirectUrl)
  }

  // Auth route with session - redirect to dashboard
  if (isAuthRoute && session) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  // Homepage with session - redirect to dashboard
  if (isHomepage && session) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return response
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (images, etc.)
     * - api routes
     * - auth callback
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$|api|auth/callback).*)',
  ],
}

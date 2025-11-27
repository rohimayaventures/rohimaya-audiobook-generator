'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { createBrowserClient } from '@supabase/ssr'

interface AuthWrapperProps {
  children: React.ReactNode
}

// Session timeout settings
const SESSION_TIMEOUT_MS = 30 * 60 * 1000 // 30 minutes
const WARNING_BEFORE_TIMEOUT_MS = 5 * 60 * 1000 // Show warning 5 minutes before timeout
const ACTIVITY_CHECK_INTERVAL_MS = 60 * 1000 // Check every minute

/**
 * AuthWrapper - Protects routes that require authentication
 *
 * Features:
 * - Redirects to /login if user is not authenticated
 * - Tracks user activity (mouse, keyboard, scroll, touch)
 * - Auto-logout after 30 minutes of inactivity
 * - Shows warning 5 minutes before auto-logout
 * - Listens for auth state changes
 */
export function AuthWrapper({ children }: AuthWrapperProps) {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(0)

  const lastActivityRef = useRef(Date.now())
  const timeoutWarningRef = useRef<NodeJS.Timeout | null>(null)
  const logoutTimerRef = useRef<NodeJS.Timeout | null>(null)

  const supabaseRef = useRef(
    createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
  )

  // Update last activity timestamp
  const updateActivity = useCallback(() => {
    lastActivityRef.current = Date.now()
    setShowTimeoutWarning(false)

    // Update cookie for server-side middleware
    document.cookie = `af_last_activity=${Date.now()}; path=/; max-age=86400; samesite=lax`
  }, [])

  // Handle logout
  const handleLogout = useCallback(async () => {
    const supabase = supabaseRef.current
    await supabase.auth.signOut()
    router.push('/login?message=session_expired')
  }, [router])

  // Extend session
  const extendSession = useCallback(() => {
    updateActivity()
    setShowTimeoutWarning(false)
  }, [updateActivity])

  // Check session and activity
  useEffect(() => {
    const supabase = supabaseRef.current

    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession()

      if (!session) {
        router.push('/login')
      } else {
        setIsAuthenticated(true)
        updateActivity()
      }
      setIsLoading(false)
    }

    checkAuth()

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (event === 'SIGNED_OUT' || !session) {
          setIsAuthenticated(false)
          router.push('/login')
        } else if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
          setIsAuthenticated(true)
          updateActivity()
        }
      }
    )

    return () => {
      subscription.unsubscribe()
    }
  }, [router, updateActivity])

  // Activity tracking
  useEffect(() => {
    if (!isAuthenticated) return

    const activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart', 'mousemove']

    // Throttled activity handler
    let throttleTimeout: NodeJS.Timeout | null = null
    const throttledUpdateActivity = () => {
      if (!throttleTimeout) {
        throttleTimeout = setTimeout(() => {
          updateActivity()
          throttleTimeout = null
        }, 1000) // Throttle to once per second
      }
    }

    // Add event listeners
    activityEvents.forEach(event => {
      window.addEventListener(event, throttledUpdateActivity, { passive: true })
    })

    // Check for timeout periodically
    const checkTimeout = () => {
      const now = Date.now()
      const timeSinceActivity = now - lastActivityRef.current
      const timeUntilTimeout = SESSION_TIMEOUT_MS - timeSinceActivity

      if (timeUntilTimeout <= 0) {
        // Session timed out
        handleLogout()
      } else if (timeUntilTimeout <= WARNING_BEFORE_TIMEOUT_MS) {
        // Show warning
        setShowTimeoutWarning(true)
        setTimeRemaining(Math.ceil(timeUntilTimeout / 1000))
      }
    }

    const intervalId = setInterval(checkTimeout, ACTIVITY_CHECK_INTERVAL_MS)

    // Update countdown timer when warning is shown
    const countdownInterval = setInterval(() => {
      if (showTimeoutWarning) {
        const now = Date.now()
        const timeSinceActivity = now - lastActivityRef.current
        const timeUntilTimeout = SESSION_TIMEOUT_MS - timeSinceActivity
        setTimeRemaining(Math.max(0, Math.ceil(timeUntilTimeout / 1000)))
      }
    }, 1000)

    return () => {
      activityEvents.forEach(event => {
        window.removeEventListener(event, throttledUpdateActivity)
      })
      if (throttleTimeout) clearTimeout(throttleTimeout)
      clearInterval(intervalId)
      clearInterval(countdownInterval)
      if (timeoutWarningRef.current) clearTimeout(timeoutWarningRef.current)
      if (logoutTimerRef.current) clearTimeout(logoutTimerRef.current)
    }
  }, [isAuthenticated, updateActivity, handleLogout, showTimeoutWarning])

  // Format remaining time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-af-purple border-t-transparent rounded-full animate-spin" />
          <p className="text-white/60 text-sm">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render children if not authenticated (redirect will happen)
  if (!isAuthenticated) {
    return null
  }

  return (
    <>
      {/* Session Timeout Warning Modal */}
      {showTimeoutWarning && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="bg-af-card border border-af-card-border rounded-2xl p-8 max-w-md mx-4 shadow-2xl">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-yellow-500/20 flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-yellow-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>

              <h3 className="text-xl font-bold text-white mb-2">
                Session Expiring Soon
              </h3>

              <p className="text-white/60 mb-4">
                Your session will expire in{' '}
                <span className="font-mono text-yellow-500 font-bold">
                  {formatTime(timeRemaining)}
                </span>{' '}
                due to inactivity.
              </p>

              <p className="text-white/40 text-sm mb-6">
                Click below to stay logged in, or you will be automatically signed out
                to protect your account.
              </p>

              <div className="flex gap-3 justify-center">
                <button
                  onClick={handleLogout}
                  className="px-6 py-3 rounded-xl bg-white/10 text-white hover:bg-white/20 transition-colors"
                >
                  Log Out Now
                </button>
                <button
                  onClick={extendSession}
                  className="px-6 py-3 rounded-xl bg-af-purple text-white hover:bg-af-purple/90 transition-colors font-semibold"
                >
                  Stay Logged In
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {children}
    </>
  )
}

export default AuthWrapper

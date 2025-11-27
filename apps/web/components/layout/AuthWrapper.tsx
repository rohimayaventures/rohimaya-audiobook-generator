'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createBrowserClient } from '@supabase/ssr'

interface AuthWrapperProps {
  children: React.ReactNode
}

/**
 * AuthWrapper - Protects routes that require authentication
 * Redirects to /login if user is not authenticated
 *
 * Usage: Wrap any page component that requires auth
 */
export function AuthWrapper({ children }: AuthWrapperProps) {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = createBrowserClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
      )

      const { data: { session } } = await supabase.auth.getSession()

      if (!session) {
        router.push('/login')
      } else {
        setIsAuthenticated(true)
      }
      setIsLoading(false)
    }

    checkAuth()
  }, [router])

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

  return <>{children}</>
}

export default AuthWrapper

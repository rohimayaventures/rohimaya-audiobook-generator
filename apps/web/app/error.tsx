'use client'

import { useEffect } from 'react'
import { GlassCard } from '@/components/ui/GlassCard'
import { PrimaryButton } from '@/components/ui/PrimaryButton'
import { SecondaryButton } from '@/components/ui/SecondaryButton'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to console for debugging
    console.error('Application error:', error)
  }, [error])

  return (
    <div className="min-h-screen bg-af-dark flex items-center justify-center p-6">
      <GlassCard className="max-w-lg w-full text-center p-8">
        {/* Error Icon */}
        <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-red-500/20 flex items-center justify-center">
          <svg
            className="w-10 h-10 text-red-400"
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

        {/* Error Message */}
        <h1 className="text-2xl font-bold text-white mb-3">
          Something went wrong
        </h1>
        <p className="text-af-text-muted mb-6">
          We encountered an unexpected error. Don't worry, your audiobooks are safe.
        </p>

        {/* Error Details (development only) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mb-6 p-4 bg-red-500/10 rounded-lg text-left">
            <p className="text-sm text-red-400 font-mono break-all">
              {error.message}
            </p>
            {error.digest && (
              <p className="text-xs text-af-text-muted mt-2">
                Error ID: {error.digest}
              </p>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <PrimaryButton onClick={reset}>
            Try Again
          </PrimaryButton>
          <SecondaryButton href="/dashboard">
            Back to Dashboard
          </SecondaryButton>
        </div>

        {/* Help Text */}
        <p className="text-sm text-af-text-muted mt-6">
          If this problem persists, please{' '}
          <a
            href="mailto:support@authorflowstudios.com"
            className="text-af-purple hover:text-af-purple-soft transition-colors"
          >
            contact support
          </a>
        </p>
      </GlassCard>
    </div>
  )
}

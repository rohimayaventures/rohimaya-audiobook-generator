'use client'

import Link from 'next/link'
import { GlassCard, PrimaryButton, SecondaryButton } from '@/components/ui'

/**
 * Billing Cancel Page - AuthorFlow Studios
 * Shown when user cancels Stripe Checkout
 */
export default function BillingCancelPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <GlassCard className="text-center">
          {/* Info icon */}
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-yellow-500/20 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-yellow-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>

          <h1 className="text-2xl font-bold text-white mb-2">
            Checkout Canceled
          </h1>

          <p className="text-white/60 mb-6">
            No worries! Your checkout was canceled and you haven&apos;t been charged.
            You can try again whenever you&apos;re ready.
          </p>

          <div className="space-y-3">
            <PrimaryButton href="/pricing" className="w-full">
              Back to Pricing
            </PrimaryButton>
            <SecondaryButton href="/dashboard" className="w-full">
              Go to Dashboard
            </SecondaryButton>
          </div>

          <p className="mt-6 text-white/40 text-sm">
            Have questions?{' '}
            <Link href="/contact" className="text-af-purple-soft hover:text-white transition-colors">
              Contact us
            </Link>
          </p>
        </GlassCard>
      </div>
    </div>
  )
}

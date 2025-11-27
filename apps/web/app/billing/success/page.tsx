'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { GlassCard, PrimaryButton } from '@/components/ui'
import { getBillingInfo, BillingInfo, getPlanDisplayName } from '@/lib/billing'
import { createClient } from '@/lib/supabaseClient'

/**
 * Billing Success Page - AuthorFlow Studios
 * Shown after successful Stripe Checkout
 */
export default function BillingSuccessPage() {
  const searchParams = useSearchParams()
  const sessionId = searchParams.get('session_id')

  const [billing, setBilling] = useState<BillingInfo | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Wait a moment for webhook to process
    const timer = setTimeout(loadBillingInfo, 2000)
    return () => clearTimeout(timer)
  }, [])

  const loadBillingInfo = async () => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (session) {
        const info = await getBillingInfo(session.access_token)
        setBilling(info)
      }
    } catch (err) {
      console.error('Error loading billing info:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <GlassCard className="text-center">
          {/* Success icon */}
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-green-500/20 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-green-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>

          <h1 className="text-2xl font-bold text-white mb-2">
            Welcome to AuthorFlow!
          </h1>

          {loading ? (
            <p className="text-white/60 mb-6">
              Setting up your subscription...
            </p>
          ) : billing ? (
            <>
              <p className="text-white/60 mb-2">
                Your subscription is now active.
              </p>
              <p className="text-af-lavender font-semibold mb-6">
                {getPlanDisplayName(billing.plan_id)} Plan
              </p>
            </>
          ) : (
            <p className="text-white/60 mb-6">
              Your subscription is being processed.
            </p>
          )}

          <div className="space-y-3">
            <PrimaryButton href="/dashboard" className="w-full">
              Go to Dashboard
            </PrimaryButton>
            <Link
              href="/billing"
              className="block text-white/60 hover:text-white transition-colors text-sm"
            >
              View billing details
            </Link>
          </div>

          {sessionId && (
            <p className="mt-6 text-white/30 text-xs">
              Session: {sessionId.slice(0, 20)}...
            </p>
          )}
        </GlassCard>
      </div>
    </div>
  )
}

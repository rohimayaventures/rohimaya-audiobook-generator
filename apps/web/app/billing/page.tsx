'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { GlassCard, PrimaryButton, SecondaryButton } from '@/components/ui'
import { getBillingInfo, createPortalSession, BillingInfo, getPlanDisplayName, getPlanBadgeColor, formatLimit } from '@/lib/billing'
import { createClient } from '@/lib/supabaseClient'

/**
 * Billing Page - AuthorFlow Studios
 * Shows current subscription status and allows management
 */
export default function BillingPage() {
  const router = useRouter()
  const [billing, setBilling] = useState<BillingInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [portalLoading, setPortalLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadBillingInfo()
  }, [])

  const loadBillingInfo = async () => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session) {
        router.push('/login?redirect=/billing')
        return
      }

      const info = await getBillingInfo(session.access_token)
      setBilling(info)
    } catch (err) {
      console.error('Error loading billing info:', err)
      setError('Failed to load billing information')
    } finally {
      setLoading(false)
    }
  }

  const handleManageBilling = async () => {
    setPortalLoading(true)
    setError('')

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session) {
        router.push('/login?redirect=/billing')
        return
      }

      const result = await createPortalSession(session.access_token)
      window.open(result.url, '_blank')
    } catch (err) {
      console.error('Portal error:', err)
      setError(err instanceof Error ? err.message : 'Failed to open billing portal')
    } finally {
      setPortalLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-white/60">Loading billing information...</div>
      </div>
    )
  }

  const isPaidPlan = billing && billing.plan_id !== 'free'
  const periodEndDate = billing?.current_period_end
    ? new Date(billing.current_period_end).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : null

  return (
    <div className="min-h-screen py-16 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/dashboard" className="text-white/60 hover:text-white transition-colors text-sm mb-4 inline-block">
            &larr; Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold text-white">Billing & Subscription</h1>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
            {error}
          </div>
        )}

        {/* Current Plan */}
        <GlassCard className="mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h2 className="text-xl font-semibold text-white">Current Plan</h2>
                <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getPlanBadgeColor(billing?.plan_id || 'free')}`}>
                  {getPlanDisplayName(billing?.plan_id || 'free')}
                </span>
                {billing?.is_admin && (
                  <span className="px-3 py-1 rounded-full text-xs font-medium border bg-red-500/20 text-red-400 border-red-500/30">
                    Admin
                  </span>
                )}
              </div>
              <p className="text-white/60">
                {billing?.status === 'active' && 'Your subscription is active.'}
                {billing?.status === 'trialing' && 'You are on a free trial.'}
                {billing?.status === 'past_due' && 'Payment past due. Please update your payment method.'}
                {billing?.status === 'canceled' && 'Your subscription has been canceled.'}
                {billing?.status === 'inactive' && !billing?.is_admin && "You're on the free plan."}
                {billing?.is_admin && 'You have full admin access.'}
              </p>
              {billing?.cancel_at_period_end && periodEndDate && (
                <p className="text-yellow-400 mt-2">
                  Your subscription will end on {periodEndDate}
                </p>
              )}
              {isPaidPlan && !billing?.cancel_at_period_end && periodEndDate && (
                <p className="text-white/40 mt-2 text-sm">
                  Next billing date: {periodEndDate}
                </p>
              )}
            </div>

            <div className="flex gap-3">
              {isPaidPlan && (
                <SecondaryButton
                  onClick={handleManageBilling}
                  loading={portalLoading}
                  disabled={portalLoading}
                >
                  Manage Subscription
                </SecondaryButton>
              )}
              {!isPaidPlan && !billing?.is_admin && (
                <PrimaryButton href="/pricing">
                  Upgrade Plan
                </PrimaryButton>
              )}
            </div>
          </div>
        </GlassCard>

        {/* Entitlements */}
        {billing?.entitlements && (
          <GlassCard className="mb-6">
            <h2 className="text-xl font-semibold text-white mb-4">Your Plan Features</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-white/5">
                <div className="text-white/60 text-sm mb-1">Projects per Month</div>
                <div className="text-white font-semibold">
                  {formatLimit(billing.entitlements.max_projects_per_month)}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-white/5">
                <div className="text-white/60 text-sm mb-1">Max Minutes per Book</div>
                <div className="text-white font-semibold">
                  {formatLimit(billing.entitlements.max_minutes_per_book)}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-white/5">
                <div className="text-white/60 text-sm mb-1">Findaway Packages</div>
                <div className="text-white font-semibold">
                  {billing.entitlements.findaway_package ? 'Included' : 'Not available'}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-white/5">
                <div className="text-white/60 text-sm mb-1">Cover Generation</div>
                <div className="text-white font-semibold">
                  {billing.entitlements.cover_generation === 'premium'
                    ? 'Premium'
                    : billing.entitlements.cover_generation
                    ? 'Included'
                    : 'Not available'}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-white/5">
                <div className="text-white/60 text-sm mb-1">Dual Voice</div>
                <div className="text-white font-semibold">
                  {billing.entitlements.dual_voice ? 'Included' : 'Not available'}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-white/5">
                <div className="text-white/60 text-sm mb-1">Priority Queue</div>
                <div className="text-white font-semibold">
                  {billing.entitlements.faster_queue ? 'Included' : 'Not available'}
                </div>
              </div>
            </div>
          </GlassCard>
        )}

        {/* Upgrade CTA for free users */}
        {!isPaidPlan && !billing?.is_admin && (
          <GlassCard className="bg-gradient-to-r from-af-purple-soft/20 to-af-lavender/20 border-af-purple-soft/30">
            <div className="text-center py-4">
              <h3 className="text-xl font-semibold text-white mb-2">
                Upgrade to unlock more features
              </h3>
              <p className="text-white/60 mb-4">
                Get unlimited audiobooks, dual-voice narration, AI cover generation, and more.
              </p>
              <PrimaryButton href="/pricing">
                View Plans
              </PrimaryButton>
            </div>
          </GlassCard>
        )}

        {/* Help section */}
        <div className="mt-8 text-center text-white/40 text-sm">
          <p>
            Need help with billing?{' '}
            <Link href="/contact" className="text-af-purple-soft hover:text-white transition-colors">
              Contact support
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { GlassCard, PrimaryButton, SecondaryButton } from '@/components/ui'
import { createCheckoutSession, PLANS, getPlanBadgeColor } from '@/lib/billing'
import { createClient } from '@/lib/supabaseClient'

/**
 * Pricing Page - AuthorFlow Studios
 * Displays subscription tiers and handles checkout flow
 */
export default function PricingPage() {
  const router = useRouter()
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('monthly')

  const handleSelectPlan = async (planId: string) => {
    if (planId === 'free') {
      // Free plan - just go to dashboard
      router.push('/dashboard')
      return
    }

    setLoading(planId)
    setError('')

    try {
      // Check if user is logged in
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session) {
        // Redirect to login with return URL
        router.push(`/login?redirect=/pricing&plan=${planId}&interval=${billingInterval}`)
        return
      }

      // Create checkout session with selected billing interval
      const result = await createCheckoutSession(
        session.access_token,
        planId,
        billingInterval
      )

      // Redirect to Stripe Checkout
      window.location.href = result.url
    } catch (err) {
      console.error('Checkout error:', err)
      setError(err instanceof Error ? err.message : 'Failed to start checkout')
      setLoading(null)
    }
  }

  const planOrder = ['free', 'creator', 'author_pro', 'publisher']

  return (
    <div className="min-h-screen py-16 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <Link href="/" className="inline-block mb-6">
            <span className="font-serif text-3xl font-bold text-gradient">
              AuthorFlow
            </span>
          </Link>
          <h1 className="text-4xl font-bold text-white mb-4">
            Choose Your Plan
          </h1>
          <p className="text-white/60 text-lg max-w-2xl mx-auto">
            Transform your manuscripts into professional audiobooks.
            Start free and upgrade as you grow.
          </p>

          {/* Billing interval toggle */}
          <div className="mt-8 flex items-center justify-center gap-4">
            <span className={`text-sm ${billingInterval === 'monthly' ? 'text-white' : 'text-white/60'}`}>
              Monthly
            </span>
            <button
              onClick={() => setBillingInterval(billingInterval === 'monthly' ? 'yearly' : 'monthly')}
              className={`relative w-14 h-7 rounded-full transition-colors ${
                billingInterval === 'yearly' ? 'bg-af-purple' : 'bg-white/20'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-6 h-6 rounded-full bg-white transition-transform ${
                  billingInterval === 'yearly' ? 'translate-x-7' : ''
                }`}
              />
            </button>
            <span className={`text-sm ${billingInterval === 'yearly' ? 'text-white' : 'text-white/60'}`}>
              Yearly
            </span>
            {billingInterval === 'yearly' && (
              <span className="ml-2 px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs font-medium">
                2 months free
              </span>
            )}
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="max-w-md mx-auto mb-8 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-center">
            {error}
          </div>
        )}

        {/* Pricing cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {planOrder.map((planId) => {
            const plan = PLANS[planId]
            if (!plan) return null

            const isHighlighted = plan.highlight
            const isLoading = loading === planId

            return (
              <div
                key={planId}
                className={`relative rounded-2xl ${
                  isHighlighted
                    ? 'ring-2 ring-af-purple-soft shadow-lg shadow-af-purple-soft/20'
                    : ''
                }`}
              >
                {isHighlighted && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-af-purple-soft text-white text-xs font-semibold rounded-full">
                    Most Popular
                  </div>
                )}

                <GlassCard className={`h-full flex flex-col ${isHighlighted ? 'border-af-purple-soft' : ''}`}>
                  {/* Plan header */}
                  <div className="text-center mb-6">
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${getPlanBadgeColor(planId)}`}>
                      {plan.name}
                    </span>
                    <div className="mt-4">
                      {billingInterval === 'yearly' && plan.price_yearly > 0 ? (
                        <>
                          <span className="text-4xl font-bold text-white">
                            ${Math.round(plan.price_yearly / 12)}
                          </span>
                          <span className="text-white/60">/month</span>
                          <div className="text-xs text-white/40 mt-1">
                            ${plan.price_yearly}/year
                          </div>
                        </>
                      ) : (
                        <>
                          <span className="text-4xl font-bold text-white">
                            ${plan.price_monthly}
                          </span>
                          {plan.price_monthly > 0 && (
                            <span className="text-white/60">/month</span>
                          )}
                        </>
                      )}
                    </div>
                    {billingInterval === 'yearly' && plan.yearly_savings && (
                      <div className="mt-2">
                        <span className="inline-block px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs font-medium">
                          {plan.yearly_savings}
                        </span>
                      </div>
                    )}
                    <p className="mt-2 text-white/60 text-sm">
                      {plan.description}
                    </p>
                    {plan.trial_days > 0 && (
                      <p className="mt-1 text-amber-400 text-xs font-medium">
                        {plan.trial_days}-day free trial
                      </p>
                    )}
                  </div>

                  {/* Features list */}
                  <ul className="space-y-3 flex-1 mb-6">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start gap-2 text-white/80 text-sm">
                        <svg
                          className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5"
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
                        {feature}
                      </li>
                    ))}
                  </ul>

                  {/* CTA button */}
                  {planId === 'free' ? (
                    <SecondaryButton
                      onClick={() => handleSelectPlan(planId)}
                      disabled={!!loading}
                      className="w-full"
                    >
                      Get Started Free
                    </SecondaryButton>
                  ) : (
                    <PrimaryButton
                      onClick={() => handleSelectPlan(planId)}
                      loading={isLoading}
                      disabled={!!loading}
                      className={`w-full ${isHighlighted ? '' : 'bg-white/10 hover:bg-white/20'}`}
                    >
                      {isLoading ? 'Loading...' : plan.trial_days > 0 ? `Start ${plan.trial_days}-day free trial` : `Start ${plan.name}`}
                    </PrimaryButton>
                  )}
                </GlassCard>
              </div>
            )
          })}
        </div>

        {/* FAQ section */}
        <div className="mt-16 max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-white text-center mb-8">
            Frequently Asked Questions
          </h2>

          <div className="space-y-4">
            <GlassCard>
              <h3 className="text-lg font-semibold text-white mb-2">
                Can I cancel anytime?
              </h3>
              <p className="text-white/60">
                Yes! You can cancel your subscription at any time from your billing settings.
                You&apos;ll continue to have access until the end of your current billing period.
              </p>
            </GlassCard>

            <GlassCard>
              <h3 className="text-lg font-semibold text-white mb-2">
                What payment methods do you accept?
              </h3>
              <p className="text-white/60">
                We accept all major credit cards (Visa, Mastercard, American Express)
                through our secure payment processor, Stripe.
              </p>
            </GlassCard>

            <GlassCard>
              <h3 className="text-lg font-semibold text-white mb-2">
                Can I upgrade or downgrade my plan?
              </h3>
              <p className="text-white/60">
                Absolutely! You can change your plan at any time from your billing settings.
                When upgrading, you&apos;ll be prorated for the remainder of your billing cycle.
              </p>
            </GlassCard>

            <GlassCard>
              <h3 className="text-lg font-semibold text-white mb-2">
                What is a Findaway-ready package?
              </h3>
              <p className="text-white/60">
                Findaway is a major audiobook distribution platform. Our Findaway-ready packages
                include all the files and metadata you need to publish your audiobook to
                retailers like Audible, Apple Books, and more.
              </p>
            </GlassCard>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <p className="text-white/60 mb-4">
            Have questions? We&apos;re here to help.
          </p>
          <Link href="/contact" className="text-af-purple-soft hover:text-white transition-colors">
            Contact Support
          </Link>
        </div>
      </div>
    </div>
  )
}

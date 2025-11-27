/**
 * Billing API client for AuthorFlow Studios
 *
 * Provides functions to interact with the backend billing endpoints:
 * - Get current billing info
 * - Create checkout session
 * - Create billing portal session
 * - Get available plans
 */

const ENGINE_API_URL = process.env.NEXT_PUBLIC_ENGINE_API_URL || 'http://localhost:8000'

export interface Entitlements {
  max_projects_per_month: number | null
  max_minutes_per_book: number | null
  findaway_package: boolean
  retail_sample: boolean | string
  cover_generation: boolean | string
  dual_voice: boolean
  faster_queue: boolean
  team_members: number | null
  team_access: boolean
  support_level: string
}

export interface UsageInfo {
  projects_created: number
  minutes_generated: number
  period_start: string
  period_end: string
}

export interface BillingInfo {
  plan_id: string
  plan_name?: string
  status: string
  current_period_end: string | null
  cancel_at_period_end: boolean
  entitlements: Entitlements
  is_admin: boolean
  stripe_customer_id: string | null
  usage?: UsageInfo
}

export interface PlanInfo {
  name: string
  price_monthly: number
  description: string
  highlight: boolean
  features: string[]
}

export interface PlansResponse {
  plans: Record<string, PlanInfo>
}

export interface CheckoutSessionResponse {
  url: string
  session_id: string
}

export interface PortalSessionResponse {
  url: string
}

/**
 * Get current user's billing information
 */
export async function getBillingInfo(accessToken: string): Promise<BillingInfo> {
  const response = await fetch(`${ENGINE_API_URL}/billing/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch billing info' }))
    throw new Error(error.detail || 'Failed to fetch billing info')
  }

  return response.json()
}

/**
 * Get available subscription plans
 */
export async function getPlans(): Promise<PlansResponse> {
  const response = await fetch(`${ENGINE_API_URL}/billing/plans`, {
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error('Failed to fetch plans')
  }

  return response.json()
}

/**
 * Create a Stripe Checkout session for subscription
 */
export async function createCheckoutSession(
  accessToken: string,
  planId: string,
  billingPeriod: 'monthly' | 'yearly' = 'monthly'
): Promise<CheckoutSessionResponse> {
  const response = await fetch(`${ENGINE_API_URL}/billing/create-checkout-session`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      plan_id: planId,
      billing_period: billingPeriod,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create checkout session' }))
    throw new Error(error.detail || 'Failed to create checkout session')
  }

  return response.json()
}

/**
 * Create a Stripe Billing Portal session
 */
export async function createPortalSession(accessToken: string): Promise<PortalSessionResponse> {
  const response = await fetch(`${ENGINE_API_URL}/billing/create-portal-session`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create portal session' }))
    throw new Error(error.detail || 'Failed to create portal session')
  }

  return response.json()
}

/**
 * Plan display information (frontend fallback)
 */
export const PLANS: Record<string, PlanInfo> = {
  free: {
    name: 'Free',
    price_monthly: 0,
    description: 'Try AuthorFlow with limited features',
    highlight: false,
    features: [
      '1 audiobook per month',
      'Up to 5 minutes per book',
      'Basic retail sample',
      'Community support',
    ],
  },
  creator: {
    name: 'Creator',
    price_monthly: 29,
    description: 'Perfect for indie authors',
    highlight: false,
    features: [
      '3 audiobooks per month',
      'Up to 1 hour per book',
      'Findaway-ready packages',
      'AI cover generation',
      'Retail sample selection',
      'Email support',
    ],
  },
  author_pro: {
    name: 'Author Pro',
    price_monthly: 79,
    description: 'For serious authors',
    highlight: true,
    features: [
      'Unlimited audiobooks',
      'Up to 6 hours per book',
      'Dual-voice narration',
      'Advanced retail samples',
      'Premium cover generation',
      'Priority queue',
      'Priority support',
    ],
  },
  publisher: {
    name: 'Publisher',
    price_monthly: 249,
    description: 'For publishers & production houses',
    highlight: false,
    features: [
      'Everything in Author Pro',
      'Unlimited book length',
      'Team access (5 members)',
      'Dedicated support',
      'Custom branding options',
      'API access',
    ],
  },
}

/**
 * Check if a feature is available for a plan
 */
export function hasFeature(entitlements: Entitlements, feature: keyof Entitlements): boolean {
  const value = entitlements[feature]
  if (value === null) return true // null means unlimited
  if (typeof value === 'string') return true // string values like "advanced" mean enabled
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value > 0
  return false
}

/**
 * Format a limit value for display
 */
export function formatLimit(value: number | null): string {
  if (value === null) return 'Unlimited'
  return value.toString()
}

/**
 * Get plan badge color
 */
export function getPlanBadgeColor(planId: string): string {
  switch (planId) {
    case 'admin':
      return 'bg-red-500/20 text-red-400 border-red-500/30'
    case 'publisher':
      return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
    case 'author_pro':
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
    case 'creator':
      return 'bg-green-500/20 text-green-400 border-green-500/30'
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  }
}

/**
 * Get display name for a plan
 */
export function getPlanDisplayName(planId: string): string {
  const names: Record<string, string> = {
    free: 'Free',
    creator: 'Creator',
    author_pro: 'Author Pro',
    publisher: 'Publisher',
    admin: 'Admin',
  }
  return names[planId] || planId
}

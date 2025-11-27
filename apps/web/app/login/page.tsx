'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { GlassCard } from '@/components/ui'
import { PrimaryButton, SecondaryButton } from '@/components/ui'
import { signIn, signInWithMagicLink } from '@/lib/auth'

/**
 * Login Page - AuthorFlow Studios
 * Email/password login with optional magic link
 */
export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [magicLinkSent, setMagicLinkSent] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const result = await signIn(email, password)

    if (result.success) {
      router.push('/dashboard')
    } else {
      setError(result.error?.message || 'Login failed')
    }

    setLoading(false)
  }

  const handleMagicLink = async () => {
    if (!email) {
      setError('Please enter your email first')
      return
    }

    setLoading(true)
    setError('')

    const result = await signInWithMagicLink(email)

    if (result.success) {
      setMagicLinkSent(true)
    } else {
      setError(result.error?.message || 'Failed to send magic link')
    }

    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-block">
            <span className="font-serif text-3xl font-bold text-gradient">
              AuthorFlow
            </span>
          </Link>
          <p className="text-white/60 mt-2">Welcome back</p>
        </div>

        <GlassCard>
          {magicLinkSent ? (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">✉️</div>
              <h2 className="text-xl font-semibold text-white mb-2">
                Check your email
              </h2>
              <p className="text-white/60 mb-6">
                We sent a magic link to <span className="text-af-lavender">{email}</span>
              </p>
              <button
                onClick={() => setMagicLinkSent(false)}
                className="text-af-purple-soft hover:text-white transition-colors"
              >
                Try a different method
              </button>
            </div>
          ) : (
            <form onSubmit={handleLogin} className="space-y-6">
              <h1 className="text-2xl font-bold text-white text-center mb-6">
                Log in to your account
              </h1>

              {/* Error message */}
              {error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  {error}
                </div>
              )}

              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-white/80 mb-2">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field"
                  placeholder="you@example.com"
                  required
                />
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-white/80 mb-2">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field"
                  placeholder="••••••••"
                  required
                />
              </div>

              {/* Submit */}
              <PrimaryButton
                type="submit"
                loading={loading}
                disabled={loading}
                className="w-full"
              >
                Log in
              </PrimaryButton>

              {/* Magic link option */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-af-card-border" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-af-midnight text-white/40">or</span>
                </div>
              </div>

              <SecondaryButton
                type="button"
                onClick={handleMagicLink}
                disabled={loading}
                className="w-full"
              >
                Continue with magic link
              </SecondaryButton>

              {/* Sign up link */}
              <p className="text-center text-white/60 text-sm">
                Don&apos;t have an account?{' '}
                <Link href="/signup" className="text-af-purple-soft hover:text-white transition-colors">
                  Sign up
                </Link>
              </p>
            </form>
          )}
        </GlassCard>
      </div>
    </div>
  )
}

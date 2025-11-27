'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { GlassCard } from '@/components/ui'
import { PrimaryButton } from '@/components/ui'
import { signUp } from '@/lib/auth'

/**
 * Signup Page - AuthorFlow Studios
 * Email/password registration
 */
export default function SignupPage() {
  const router = useRouter()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validate display name
    if (!displayName.trim()) {
      setError('Please enter your name')
      return
    }

    // Validate password match
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    // Validate password length
    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setLoading(true)

    const result = await signUp(email, password, displayName.trim())

    if (result.success) {
      setSuccess(true)
    } else {
      setError(result.error?.message || 'Signup failed')
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
          <p className="text-white/60 mt-2">Create your account</p>
        </div>

        <GlassCard>
          {success ? (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">🎉</div>
              <h2 className="text-xl font-semibold text-white mb-2">
                Check your email
              </h2>
              <p className="text-white/60 mb-6">
                We sent a confirmation link to <span className="text-af-lavender">{email}</span>
              </p>
              <p className="text-white/40 text-sm">
                Click the link in the email to verify your account and get started.
              </p>
              <Link
                href="/login"
                className="inline-block mt-6 text-af-purple-soft hover:text-white transition-colors"
              >
                Back to login
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSignup} className="space-y-6">
              <h1 className="text-2xl font-bold text-white text-center mb-6">
                Get started for free
              </h1>

              {/* Error message */}
              {error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  {error}
                </div>
              )}

              {/* Display Name */}
              <div>
                <label htmlFor="displayName" className="block text-sm font-medium text-white/80 mb-2">
                  Your Name
                </label>
                <input
                  id="displayName"
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="input-field"
                  placeholder="John Doe"
                  required
                />
              </div>

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
                  minLength={6}
                  required
                />
                <p className="text-white/40 text-xs mt-1">At least 6 characters</p>
              </div>

              {/* Confirm Password */}
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-white/80 mb-2">
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
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
                Create account
              </PrimaryButton>

              {/* Terms */}
              <p className="text-center text-white/40 text-xs">
                By signing up, you agree to our Terms of Service and Privacy Policy
              </p>

              {/* Login link */}
              <p className="text-center text-white/60 text-sm">
                Already have an account?{' '}
                <Link href="/login" className="text-af-purple-soft hover:text-white transition-colors">
                  Log in
                </Link>
              </p>
            </form>
          )}
        </GlassCard>
      </div>
    </div>
  )
}

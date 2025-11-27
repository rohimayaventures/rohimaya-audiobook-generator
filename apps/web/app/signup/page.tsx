'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { GlassCard } from '@/components/ui'
import { PrimaryButton } from '@/components/ui'
import { signUp, signInWithOAuth, OAuthProvider } from '@/lib/auth'

// Password validation rules
const PASSWORD_RULES = {
  minLength: { test: (p: string) => p.length >= 8, label: 'At least 8 characters' },
  hasUppercase: { test: (p: string) => /[A-Z]/.test(p), label: 'One uppercase letter' },
  hasLowercase: { test: (p: string) => /[a-z]/.test(p), label: 'One lowercase letter' },
  hasNumber: { test: (p: string) => /[0-9]/.test(p), label: 'One number' },
  hasSpecial: { test: (p: string) => /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~]/.test(p), label: 'One special character' },
}

/**
 * Signup Page - AuthorFlow Studios
 * Email/password registration with strong password requirements
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
  const [showPasswordRules, setShowPasswordRules] = useState(false)

  // Check password strength
  const passwordChecks = useMemo(() => {
    return Object.entries(PASSWORD_RULES).map(([key, rule]) => ({
      key,
      label: rule.label,
      passed: rule.test(password),
    }))
  }, [password])

  const isPasswordStrong = useMemo(() => {
    return passwordChecks.every(check => check.passed)
  }, [passwordChecks])

  const passwordStrength = useMemo(() => {
    const passedCount = passwordChecks.filter(c => c.passed).length
    if (passedCount === 0) return { level: 0, label: '', color: '' }
    if (passedCount <= 2) return { level: 1, label: 'Weak', color: 'bg-red-500' }
    if (passedCount <= 3) return { level: 2, label: 'Fair', color: 'bg-yellow-500' }
    if (passedCount <= 4) return { level: 3, label: 'Good', color: 'bg-blue-500' }
    return { level: 4, label: 'Strong', color: 'bg-green-500' }
  }, [passwordChecks])

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validate display name
    if (!displayName.trim()) {
      setError('Please enter your name')
      return
    }

    // Validate password strength
    if (!isPasswordStrong) {
      setError('Please create a stronger password that meets all requirements')
      return
    }

    // Validate password match
    if (password !== confirmPassword) {
      setError('Passwords do not match')
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

  const handleOAuth = async (provider: OAuthProvider) => {
    setLoading(true)
    setError('')

    const result = await signInWithOAuth(provider)

    if (!result.success) {
      setError(result.error?.message || `Failed to sign in with ${provider}`)
      setLoading(false)
    }
    // If successful, the page will redirect to the OAuth provider
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
                  onFocus={() => setShowPasswordRules(true)}
                  className="input-field"
                  placeholder="••••••••"
                  required
                />

                {/* Password strength bar */}
                {password.length > 0 && (
                  <div className="mt-2">
                    <div className="flex gap-1 mb-1">
                      {[1, 2, 3, 4].map((level) => (
                        <div
                          key={level}
                          className={`h-1 flex-1 rounded-full transition-colors ${
                            level <= passwordStrength.level ? passwordStrength.color : 'bg-white/10'
                          }`}
                        />
                      ))}
                    </div>
                    {passwordStrength.label && (
                      <p className={`text-xs ${
                        passwordStrength.level <= 1 ? 'text-red-400' :
                        passwordStrength.level === 2 ? 'text-yellow-400' :
                        passwordStrength.level === 3 ? 'text-blue-400' :
                        'text-green-400'
                      }`}>
                        {passwordStrength.label}
                      </p>
                    )}
                  </div>
                )}

                {/* Password requirements checklist */}
                {showPasswordRules && (
                  <div className="mt-3 p-3 rounded-lg bg-af-card border border-af-card-border">
                    <p className="text-white/60 text-xs mb-2">Password must have:</p>
                    <ul className="space-y-1">
                      {passwordChecks.map((check) => (
                        <li
                          key={check.key}
                          className={`text-xs flex items-center gap-2 ${
                            check.passed ? 'text-green-400' : 'text-white/40'
                          }`}
                        >
                          <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                            check.passed ? 'bg-green-500/20' : 'bg-white/5'
                          }`}>
                            {check.passed ? '✓' : '○'}
                          </span>
                          {check.label}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
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
                  className={`input-field ${
                    confirmPassword.length > 0
                      ? password === confirmPassword
                        ? 'border-green-500/50 focus:border-green-500'
                        : 'border-red-500/50 focus:border-red-500'
                      : ''
                  }`}
                  placeholder="••••••••"
                  required
                />
                {confirmPassword.length > 0 && password !== confirmPassword && (
                  <p className="text-red-400 text-xs mt-1">Passwords do not match</p>
                )}
                {confirmPassword.length > 0 && password === confirmPassword && (
                  <p className="text-green-400 text-xs mt-1">Passwords match</p>
                )}
              </div>

              {/* Submit */}
              <PrimaryButton
                type="submit"
                loading={loading}
                disabled={loading || !isPasswordStrong || password !== confirmPassword}
                className="w-full"
              >
                Create account
              </PrimaryButton>

              {/* Terms */}
              <p className="text-center text-white/40 text-xs">
                By signing up, you agree to our Terms of Service and Privacy Policy
              </p>

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-af-card-border" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-af-midnight text-white/40">or sign up with</span>
                </div>
              </div>

              {/* OAuth buttons */}
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => handleOAuth('google')}
                  disabled={loading}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-af-card-border bg-af-card hover:bg-af-card-hover transition-colors text-white/80 hover:text-white disabled:opacity-50"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Google
                </button>
                <button
                  type="button"
                  onClick={() => handleOAuth('github')}
                  disabled={loading}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-af-card-border bg-af-card hover:bg-af-card-hover transition-colors text-white/80 hover:text-white disabled:opacity-50"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  GitHub
                </button>
              </div>

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

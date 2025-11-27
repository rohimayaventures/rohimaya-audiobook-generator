'use client'

import { useState, useEffect } from 'react'
import { GlassCard } from '@/components/ui'
import { Footer } from '@/components/layout'
import { getCurrentUser } from '@/lib/supabaseClient'

/**
 * Contact Page - AuthorFlow Studios
 * Contact form with Brevo integration
 * Theme: Midnight Indigo Glow - Magical Tech
 */

interface FormData {
  name: string
  email: string
  subject: string
  message: string
}

type FormStatus = 'idle' | 'submitting' | 'success' | 'error'

export default function ContactPage() {
  const [user, setUser] = useState<{ email?: string } | null>(null)
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    subject: '',
    message: '',
  })
  const [status, setStatus] = useState<FormStatus>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    const checkUser = async () => {
      const currentUser = await getCurrentUser()
      setUser(currentUser)
    }
    checkUser()
  }, [])

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('submitting')
    setErrorMessage('')

    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to send message')
      }

      setStatus('success')
      setFormData({ name: '', email: '', subject: '', message: '' })
    } catch (error) {
      setStatus('error')
      setErrorMessage(error instanceof Error ? error.message : 'Something went wrong')
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-af-midnight/60 border-b border-af-card-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <a href="/" className="font-serif text-xl font-bold text-gradient">
              AuthorFlow
            </a>
            <div className="flex items-center gap-4">
              {user ? (
                <a
                  href="/dashboard"
                  className="text-sm font-medium px-4 py-2 rounded-lg bg-af-purple hover:bg-af-purple/90 transition-colors"
                >
                  Dashboard
                </a>
              ) : (
                <>
                  <a
                    href="/login"
                    className="text-sm font-medium text-white/80 hover:text-white transition-colors"
                  >
                    Log in
                  </a>
                  <a
                    href="/signup"
                    className="text-sm font-medium px-4 py-2 rounded-lg bg-af-purple hover:bg-af-purple/90 transition-colors"
                  >
                    Sign up
                  </a>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="font-serif text-4xl sm:text-5xl font-bold text-white mb-4 text-glow">
              Get in Touch
            </h1>
            <p className="text-lg text-af-lavender">
              Have questions about AuthorFlow Studios? We&apos;d love to hear from you.
            </p>
          </div>

          {/* Contact Form */}
          <GlassCard className="p-8">
            {status === 'success' ? (
              <div className="text-center py-8">
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
                <h2 className="text-2xl font-bold text-white mb-2">Message Sent!</h2>
                <p className="text-white/60 mb-6">
                  Thank you for reaching out. We&apos;ll get back to you as soon as possible.
                </p>
                <button
                  onClick={() => setStatus('idle')}
                  className="text-af-purple-soft hover:text-af-lavender transition-colors"
                >
                  Send another message
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Name */}
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-af-lavender mb-2">
                    Your Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="input-field"
                    placeholder="John Doe"
                  />
                </div>

                {/* Email */}
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-af-lavender mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="input-field"
                    placeholder="you@example.com"
                  />
                </div>

                {/* Subject */}
                <div>
                  <label htmlFor="subject" className="block text-sm font-medium text-af-lavender mb-2">
                    Subject
                  </label>
                  <select
                    id="subject"
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    required
                    className="input-field"
                  >
                    <option value="">Select a topic...</option>
                    <option value="General Inquiry">General Inquiry</option>
                    <option value="Technical Support">Technical Support</option>
                    <option value="Pricing & Plans">Pricing & Plans</option>
                    <option value="Partnership Opportunity">Partnership Opportunity</option>
                    <option value="Feature Request">Feature Request</option>
                    <option value="Bug Report">Bug Report</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                {/* Message */}
                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-af-lavender mb-2">
                    Message
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    rows={6}
                    className="input-field resize-none"
                    placeholder="Tell us how we can help..."
                  />
                </div>

                {/* Error Message */}
                {status === 'error' && (
                  <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                    <p className="text-red-400 text-sm">{errorMessage}</p>
                  </div>
                )}

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={status === 'submitting'}
                  className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {status === 'submitting' ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Sending...
                    </span>
                  ) : (
                    '✨ Send Message ✨'
                  )}
                </button>
              </form>
            )}
          </GlassCard>

          {/* Alternative Contact */}
          <div className="mt-12 text-center">
            <p className="text-white/60 mb-4">
              Prefer email? Reach us directly at
            </p>
            <a
              href="mailto:support@authorflowstudios.rohimayapublishing.com"
              className="text-af-purple-soft hover:text-af-lavender transition-colors text-lg"
            >
              support@authorflowstudios.rohimayapublishing.com
            </a>
          </div>
        </div>
      </main>

      <Footer user={user} />
    </div>
  )
}

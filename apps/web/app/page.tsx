'use client'

import { useState, useEffect } from 'react'
import { FeatureCard, GlassCard } from '@/components/ui'
import { PrimaryButton, SecondaryButton } from '@/components/ui'
import { Footer } from '@/components/layout'
import { InteractiveDemo, TutorialSection } from '@/components/landing'
import { getCurrentUser } from '@/lib/supabaseClient'

/**
 * Landing Page - AuthorFlow Studios
 * Public page with hero section, features, interactive demo, tutorial, pricing, and testimonials
 * Theme: Midnight Indigo Glow - Magical Tech
 */
export default function LandingPage() {
  const [user, setUser] = useState<{ email?: string } | null>(null)

  useEffect(() => {
    const checkUser = async () => {
      const currentUser = await getCurrentUser()
      setUser(currentUser)
    }
    checkUser()
  }, [])

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-af-midnight/60 border-b border-af-card-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <span className="font-serif text-xl font-bold text-gradient">
              AuthorFlow
            </span>
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-sm text-white/70 hover:text-white transition-colors">
                Features
              </a>
              <a href="#demo" className="text-sm text-white/70 hover:text-white transition-colors">
                Demo
              </a>
              <a href="#tutorial" className="text-sm text-white/70 hover:text-white transition-colors">
                Tutorial
              </a>
              <a href="#pricing" className="text-sm text-white/70 hover:text-white transition-colors">
                Pricing
              </a>
            </div>
            <div className="flex items-center gap-4">
              {user ? (
                <a
                  href="/dashboard"
                  className="text-sm font-medium px-4 py-2 rounded-lg bg-af-purple hover:bg-af-purple/90 transition-colors"
                >
                  Go to Dashboard
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
                    Start Free
                  </a>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1">
        {/* Hero Section */}
        <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
          {/* Background gradient orbs */}
          <div className="absolute top-20 left-1/4 w-96 h-96 bg-af-purple/20 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-af-accent/10 rounded-full blur-3xl" />

          <div className="max-w-4xl mx-auto text-center relative z-10">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-af-card border border-af-card-border mb-8">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-sm text-white/80">Now with Google Drive integration</span>
            </div>

            {/* Logo/Brand */}
            <h1 className="font-serif text-5xl sm:text-6xl lg:text-7xl font-bold text-white mb-6 text-glow">
              AuthorFlow Studios
            </h1>

            {/* Tagline */}
            <p className="text-xl sm:text-2xl text-af-lavender mb-4">
              Transform your manuscript into a studio-ready audiobook.
            </p>

            {/* Supporting text */}
            <p className="text-lg text-white/60 mb-10 max-w-2xl mx-auto">
              AI-powered audiobook production with premium voices, multi-narrator support,
              and professional-grade audio quality. No technical expertise needed.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
              <PrimaryButton href="/signup" size="lg">
                Start Free Trial
              </PrimaryButton>
              <SecondaryButton href="#demo" size="lg">
                Watch Demo
              </SecondaryButton>
            </div>

            {/* Trust badges */}
            <div className="flex items-center justify-center gap-6 mt-8 text-white/40 text-sm flex-wrap">
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                Secure & Private
              </span>
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Fast Processing
              </span>
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                </svg>
                Cloud-Based
              </span>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 border-t border-af-card-border">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-white mb-4">
                Professional Audiobook Production Made Simple
              </h2>
              <p className="text-white/60 max-w-2xl mx-auto">
                Everything you need to transform your written words into captivating audio experiences.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <FeatureCard
                icon="🎙️"
                title="Multi-Voice Narration"
                description="Create engaging audiobooks with single narrator or multi-character dialogues. Assign unique voices to each character."
              />
              <FeatureCard
                icon="🎭"
                title="Emotional TTS"
                description="AI voices that convey emotion - excitement, sadness, suspense. Bring your story to life with nuanced delivery."
              />
              <FeatureCard
                icon="📂"
                title="Google Drive Integration"
                description="Import manuscripts directly from Google Drive or Docs. Seamless workflow from writing to audiobook."
              />
              <FeatureCard
                icon="🎧"
                title="Studio-Quality Audio"
                description="Professional-grade output powered by OpenAI, ElevenLabs, and Inworld. Export in MP3, WAV, or M4B."
              />
              <FeatureCard
                icon="📖"
                title="Chapter Management"
                description="Automatic chapter detection and organization. Perfect for long-form content and full-length novels."
              />
              <FeatureCard
                icon="⚡"
                title="Fast Processing"
                description="Generate hours of audio content in minutes. Parallel processing ensures quick turnaround times."
              />
            </div>
          </div>
        </section>

        {/* Interactive Demo Section */}
        <section id="demo" className="py-20 px-4 sm:px-6 lg:px-8 bg-af-card/30">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <span className="inline-block px-4 py-1.5 rounded-full bg-af-purple/20 text-af-lavender text-sm font-medium mb-4">
                Interactive Demo
              </span>
              <h2 className="text-3xl font-bold text-white mb-4">
                See How It Works
              </h2>
              <p className="text-white/60 max-w-2xl mx-auto">
                Watch our step-by-step demo to see how easy it is to create professional audiobooks.
              </p>
            </div>

            <InteractiveDemo />
          </div>
        </section>

        {/* Tutorial Section */}
        <section id="tutorial" className="py-20 px-4 sm:px-6 lg:px-8 border-t border-af-card-border">
          <TutorialSection />
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8 bg-af-card/30">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-white mb-4">
                Simple, Transparent Pricing
              </h2>
              <p className="text-white/60 max-w-2xl mx-auto">
                Choose the plan that fits your needs. All plans include core features. Upgrade or downgrade anytime.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {/* Creator Plan */}
              <GlassCard className="p-6">
                <div className="mb-6">
                  <h3 className="text-xl font-bold text-white mb-2">Creator</h3>
                  <p className="text-white/60 text-sm">Perfect for indie authors</p>
                </div>
                <div className="mb-6">
                  <span className="text-4xl font-bold text-white">$29</span>
                  <span className="text-white/60">/month</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {[
                    '3 audiobooks per month',
                    'Up to 1 hour per book',
                    'Findaway-ready packages',
                    'Emotional TTS',
                    'Email support',
                  ].map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-sm text-white/70">
                      <svg className="w-5 h-5 text-green-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>
                <SecondaryButton href="/pricing" className="w-full">
                  Get Started
                </SecondaryButton>
              </GlassCard>

              {/* Author Pro Plan */}
              <GlassCard className="p-6 border-af-purple/50 relative">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-af-purple rounded-full text-xs font-medium text-white">
                  Most Popular
                </div>
                <div className="mb-6">
                  <h3 className="text-xl font-bold text-white mb-2">Author Pro</h3>
                  <p className="text-white/60 text-sm">For serious authors</p>
                </div>
                <div className="mb-6">
                  <span className="text-4xl font-bold text-white">$79</span>
                  <span className="text-white/60">/month</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {[
                    'Unlimited audiobooks',
                    'Up to 6 hours per book',
                    'Multi-character voices',
                    'Spicy retail samples',
                    'Premium covers',
                    'Priority support',
                  ].map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-sm text-white/70">
                      <svg className="w-5 h-5 text-green-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>
                <PrimaryButton href="/pricing" className="w-full">
                  Start Free Trial
                </PrimaryButton>
              </GlassCard>

              {/* Publisher Plan */}
              <GlassCard className="p-6">
                <div className="mb-6">
                  <h3 className="text-xl font-bold text-white mb-2">Publisher</h3>
                  <p className="text-white/60 text-sm">For publishing houses</p>
                </div>
                <div className="mb-6">
                  <span className="text-4xl font-bold text-white">$249</span>
                  <span className="text-white/60">/month</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {[
                    'Everything in Author Pro',
                    'Unlimited book length',
                    'Team access (5 members)',
                    'Custom branding',
                    'API access',
                    'Dedicated support',
                  ].map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-sm text-white/70">
                      <svg className="w-5 h-5 text-green-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>
                <SecondaryButton href="/pricing" className="w-full">
                  Contact Sales
                </SecondaryButton>
              </GlassCard>
            </div>
          </div>
        </section>

        {/* Testimonials Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 border-t border-af-card-border">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-white mb-4">
                Loved by Authors Worldwide
              </h2>
              <p className="text-white/60">
                See what authors are saying about AuthorFlow Studios
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              {[
                {
                  quote: "AuthorFlow transformed my publishing workflow. What used to take weeks now takes hours. The voice quality is incredible!",
                  author: "Sarah Mitchell",
                  role: "Bestselling Romance Author",
                },
                {
                  quote: "The multi-character feature is a game-changer for my fantasy novels. Each character has a distinct voice that brings my world to life.",
                  author: "James Chen",
                  role: "Fantasy Writer",
                },
                {
                  quote: "As a small publisher, AuthorFlow has allowed us to offer audiobooks without breaking the bank. Our catalog has tripled.",
                  author: "Maria Santos",
                  role: "Indie Publisher",
                },
              ].map((testimonial, index) => (
                <GlassCard key={index} className="p-6">
                  <div className="flex gap-1 mb-4">
                    {[...Array(5)].map((_, i) => (
                      <svg key={i} className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                      </svg>
                    ))}
                  </div>
                  <p className="text-white/80 mb-4 italic">&ldquo;{testimonial.quote}&rdquo;</p>
                  <div>
                    <p className="text-white font-medium">{testimonial.author}</p>
                    <p className="text-white/50 text-sm">{testimonial.role}</p>
                  </div>
                </GlassCard>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-af-card/30">
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-white mb-4">
                Frequently Asked Questions
              </h2>
            </div>

            <div className="space-y-4">
              {[
                {
                  q: 'How long does it take to generate an audiobook?',
                  a: 'Generation time depends on your manuscript length. A typical 80,000-word novel takes about 30-45 minutes to process. You\'ll receive an email notification when your audiobook is ready.',
                },
                {
                  q: 'What file formats do you support?',
                  a: 'We accept DOCX, PDF, TXT, and EPUB files for manuscripts. For output, you can download in MP3, WAV, or M4B (audiobook) formats.',
                },
                {
                  q: 'Can I use the audiobooks commercially?',
                  a: 'Yes! All audiobooks created with AuthorFlow Studios are yours to use commercially. Publish on Audible, ACX, Apple Books, or any other platform.',
                },
                {
                  q: 'What if I\'m not satisfied with the result?',
                  a: 'You can regenerate your audiobook with different voice settings at no extra cost. If you\'re still not satisfied, contact our support team for assistance.',
                },
                {
                  q: 'Is there a free trial?',
                  a: 'Yes! Start with our free trial to test the platform. Create your first audiobook project and experience our premium features before committing.',
                },
              ].map((faq, index) => (
                <details
                  key={index}
                  className="group bg-af-card/50 rounded-xl border border-af-card-border overflow-hidden"
                >
                  <summary className="flex items-center justify-between p-5 cursor-pointer list-none">
                    <span className="font-medium text-white">{faq.q}</span>
                    <svg
                      className="w-5 h-5 text-white/60 transition-transform group-open:rotate-180"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </summary>
                  <div className="px-5 pb-5 text-white/70">
                    {faq.a}
                  </div>
                </details>
              ))}
            </div>
          </div>
        </section>

        {/* Final CTA Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 border-t border-af-card-border">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
              Ready to Create Your Audiobook?
            </h2>
            <p className="text-lg text-white/60 mb-10">
              Join thousands of authors who are already creating professional audiobooks with AuthorFlow Studios.
              Start your free trial today - no credit card required.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <PrimaryButton href="/signup" size="lg">
                Start Free Trial
              </PrimaryButton>
              <SecondaryButton href="#demo" size="lg">
                Watch Demo
              </SecondaryButton>
            </div>
          </div>
        </section>
      </main>

      <Footer user={user} />
    </div>
  )
}

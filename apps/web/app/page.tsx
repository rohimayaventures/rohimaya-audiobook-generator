'use client'

import { useState, useEffect } from 'react'
import { FeatureCard } from '@/components/ui'
import { PrimaryButton, SecondaryButton } from '@/components/ui'
import { Footer } from '@/components/layout'
import { getCurrentUser } from '@/lib/supabaseClient'

/**
 * Landing Page - AuthorFlow Studios
 * Public page with hero section and feature highlights
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
      {/* Navigation - Simple for landing */}
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-af-midnight/60 border-b border-af-card-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <span className="font-serif text-xl font-bold text-gradient">
              AuthorFlow
            </span>
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
                    Sign up
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
        <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto text-center">
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
              and professional-grade audio quality.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
              <PrimaryButton href="/signup" size="lg">
                Get started
              </PrimaryButton>
              <SecondaryButton href="/login" size="lg">
                Log in
              </SecondaryButton>
            </div>

            {/* Note text */}
            <p className="text-sm text-white/40">
              No complex setup. Just upload, choose voices, and generate.
            </p>
          </div>
        </section>

        {/* Feature Cards Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-2xl font-bold text-white text-center mb-12">
              Everything you need to create audiobooks
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <FeatureCard
                icon="🎙️"
                title="Multi-Voice Narration"
                description="Create engaging audiobooks with single narrator or dual-voice character dialogues. Perfect for fiction with distinct character voices."
              />
              <FeatureCard
                icon="🎧"
                title="Studio-Ready Audio"
                description="Professional-grade TTS powered by OpenAI, ElevenLabs, and premium cloud providers. Export in MP3, WAV, or audiobook formats."
              />
              <FeatureCard
                icon="✨"
                title="Built for Authors & Studios"
                description="No audio engineering expertise needed. Upload your manuscript, configure your settings, and let us handle the rest."
              />
            </div>
          </div>
        </section>

        {/* How it works section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 border-t border-af-card-border">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-2xl font-bold text-white mb-12">
              How it works
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
              <div className="flex flex-col items-center">
                <div className="w-12 h-12 rounded-full bg-af-purple/20 flex items-center justify-center text-af-lavender text-xl font-bold mb-4">
                  1
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Upload</h3>
                <p className="text-white/60 text-sm">
                  Drop your manuscript file or paste your text directly
                </p>
              </div>

              <div className="flex flex-col items-center">
                <div className="w-12 h-12 rounded-full bg-af-purple/20 flex items-center justify-center text-af-lavender text-xl font-bold mb-4">
                  2
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Configure</h3>
                <p className="text-white/60 text-sm">
                  Choose your voice profile and output format
                </p>
              </div>

              <div className="flex flex-col items-center">
                <div className="w-12 h-12 rounded-full bg-af-purple/20 flex items-center justify-center text-af-lavender text-xl font-bold mb-4">
                  3
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Generate</h3>
                <p className="text-white/60 text-sm">
                  Download your studio-ready audiobook
                </p>
              </div>
            </div>

            <div className="mt-12">
              <PrimaryButton href="/signup">
                Start creating now
              </PrimaryButton>
            </div>
          </div>
        </section>
      </main>

      <Footer user={user} />
    </div>
  )
}

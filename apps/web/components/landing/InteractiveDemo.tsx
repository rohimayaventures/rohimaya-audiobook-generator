'use client'

import { useState, useEffect, useRef } from 'react'
import { GlassCard } from '@/components/ui'

interface DemoStep {
  id: number
  title: string
  description: string
  duration: number // seconds to show this step
}

const demoSteps: DemoStep[] = [
  {
    id: 1,
    title: 'Upload Your Manuscript',
    description: 'Drag and drop your file or import from Google Drive',
    duration: 5,
  },
  {
    id: 2,
    title: 'Select Your Voices',
    description: 'Choose from 50+ premium AI voices for your narration',
    duration: 5,
  },
  {
    id: 3,
    title: 'Preview & Customize',
    description: 'Listen to samples and adjust settings to your preference',
    duration: 5,
  },
  {
    id: 4,
    title: 'Generate & Download',
    description: 'Create your audiobook and download in your preferred format',
    duration: 5,
  },
]

export function InteractiveDemo() {
  const [activeStep, setActiveStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(true)
  const [progress, setProgress] = useState(0)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Auto-advance through steps
  useEffect(() => {
    if (!isPlaying) return

    const stepDuration = demoSteps[activeStep].duration * 1000
    const tickInterval = 50 // Update progress every 50ms
    let elapsed = 0

    intervalRef.current = setInterval(() => {
      elapsed += tickInterval
      setProgress((elapsed / stepDuration) * 100)

      if (elapsed >= stepDuration) {
        setActiveStep((prev) => (prev + 1) % demoSteps.length)
        setProgress(0)
        elapsed = 0
      }
    }, tickInterval)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [activeStep, isPlaying])

  const goToStep = (index: number) => {
    setActiveStep(index)
    setProgress(0)
  }

  const togglePlayPause = () => {
    setIsPlaying(!isPlaying)
  }

  return (
    <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-center">
      {/* Demo Visual Panel */}
      <div className="relative order-2 lg:order-1">
        <GlassCard className="aspect-[4/3] overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-af-purple/5 to-af-accent/5" />

          {/* Step 1: Upload */}
          <div className={`absolute inset-0 p-6 sm:p-8 flex flex-col items-center justify-center transition-all duration-500 ${activeStep === 0 ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'}`}>
            <div className="w-full max-w-sm">
              {/* Upload zone */}
              <div className="border-2 border-dashed border-af-purple/40 rounded-xl p-8 text-center hover:border-af-purple/60 transition-colors bg-af-card/30">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-af-purple/20 flex items-center justify-center">
                  <svg className="w-8 h-8 text-af-lavender" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <p className="text-white/80 font-medium mb-2">Drop your manuscript here</p>
                <p className="text-white/50 text-sm mb-4">or click to browse</p>
                <div className="flex justify-center gap-2 flex-wrap">
                  <span className="px-2 py-1 rounded bg-af-card text-xs text-white/60">.docx</span>
                  <span className="px-2 py-1 rounded bg-af-card text-xs text-white/60">.pdf</span>
                  <span className="px-2 py-1 rounded bg-af-card text-xs text-white/60">.txt</span>
                  <span className="px-2 py-1 rounded bg-af-card text-xs text-white/60">.epub</span>
                </div>
              </div>

              {/* Google Drive button */}
              <button className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg border border-af-card-border bg-af-card/50 hover:bg-af-card transition-colors">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none">
                  <path d="M4.5 14.5L8 20.5H16L12.5 14.5H4.5Z" fill="#4285F4"/>
                  <path d="M16 20.5L19.5 14.5L12 2L8.5 8L16 20.5Z" fill="#FBBC04"/>
                  <path d="M8.5 8L4.5 14.5H12.5L16 8H8.5Z" fill="#34A853"/>
                </svg>
                <span className="text-white/80 text-sm">Import from Google Drive</span>
              </button>
            </div>
          </div>

          {/* Step 2: Voice Selection */}
          <div className={`absolute inset-0 p-6 sm:p-8 flex flex-col transition-all duration-500 ${activeStep === 1 ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'}`}>
            <p className="text-white/60 text-sm mb-4">Select narrator voice:</p>
            <div className="space-y-3 flex-1 overflow-hidden">
              {[
                { name: 'Emma', style: 'Natural & Warm', selected: true, color: 'from-pink-500 to-rose-500' },
                { name: 'James', style: 'Deep & Authoritative', selected: false, color: 'from-blue-500 to-indigo-500' },
                { name: 'Sarah', style: 'Friendly & Expressive', selected: false, color: 'from-purple-500 to-violet-500' },
                { name: 'Michael', style: 'Calm & Professional', selected: false, color: 'from-green-500 to-emerald-500' },
              ].map((voice, i) => (
                <div
                  key={voice.name}
                  className={`flex items-center gap-4 p-3 rounded-xl transition-all cursor-pointer ${
                    voice.selected
                      ? 'bg-af-purple/20 border border-af-purple/50 shadow-lg shadow-af-purple/10'
                      : 'bg-af-card/30 border border-transparent hover:bg-af-card/50'
                  }`}
                >
                  <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${voice.color} flex items-center justify-center text-white font-bold shadow-lg`}>
                    {voice.name[0]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium">{voice.name}</p>
                    <p className="text-white/50 text-sm truncate">{voice.style}</p>
                  </div>
                  {voice.selected && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-af-lavender font-medium">Selected</span>
                      <svg className="w-5 h-5 text-af-lavender" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                      </svg>
                    </div>
                  )}
                  {!voice.selected && (
                    <button className="p-2 rounded-lg hover:bg-white/10 transition-colors">
                      <svg className="w-5 h-5 text-white/40" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z"/>
                      </svg>
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Step 3: Preview */}
          <div className={`absolute inset-0 p-6 sm:p-8 flex flex-col transition-all duration-500 ${activeStep === 2 ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'}`}>
            <div className="flex-1 flex flex-col justify-center">
              {/* Audio player mockup */}
              <div className="bg-af-card/50 rounded-xl p-4 mb-4">
                <div className="flex items-center gap-4 mb-4">
                  <button className="w-14 h-14 rounded-full bg-af-purple flex items-center justify-center shadow-lg shadow-af-purple/30 hover:bg-af-purple/90 transition-colors">
                    <svg className="w-6 h-6 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z"/>
                    </svg>
                  </button>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-white font-medium">Chapter 1: The Beginning</span>
                    </div>
                    <div className="h-2 bg-af-card rounded-full overflow-hidden">
                      <div className="h-full w-2/5 bg-gradient-to-r from-af-purple to-af-accent rounded-full transition-all duration-300" />
                    </div>
                    <div className="flex justify-between text-xs text-white/40 mt-1">
                      <span>1:23</span>
                      <span>3:45</span>
                    </div>
                  </div>
                </div>

                {/* Waveform visualization */}
                <div className="flex items-center justify-center gap-0.5 h-12">
                  {[...Array(40)].map((_, i) => (
                    <div
                      key={i}
                      className="w-1 bg-af-purple/60 rounded-full"
                      style={{
                        height: `${20 + Math.sin(i * 0.5) * 15 + Math.random() * 20}%`,
                        opacity: i < 16 ? 1 : 0.4,
                      }}
                    />
                  ))}
                </div>
              </div>

              {/* Settings preview */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-af-card/30 rounded-lg p-3">
                  <p className="text-white/50 text-xs mb-1">Speed</p>
                  <p className="text-white font-medium">1.0x</p>
                </div>
                <div className="bg-af-card/30 rounded-lg p-3">
                  <p className="text-white/50 text-xs mb-1">Format</p>
                  <p className="text-white font-medium">MP3 320kbps</p>
                </div>
              </div>
            </div>
          </div>

          {/* Step 4: Download */}
          <div className={`absolute inset-0 p-6 sm:p-8 flex flex-col items-center justify-center transition-all duration-500 ${activeStep === 3 ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'}`}>
            <div className="text-center">
              {/* Success animation */}
              <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-green-500/20 flex items-center justify-center animate-pulse">
                <svg className="w-12 h-12 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>

              <h3 className="text-xl font-bold text-white mb-2">Your Audiobook is Ready!</h3>
              <p className="text-white/60 text-sm mb-6">12 chapters • 4 hours 32 minutes</p>

              {/* Download options */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button className="px-6 py-3 rounded-lg bg-af-purple text-white font-medium hover:bg-af-purple/90 transition-colors flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download MP3
                </button>
                <button className="px-6 py-3 rounded-lg border border-af-card-border text-white/80 font-medium hover:bg-af-card transition-colors">
                  M4B (Audiobook)
                </button>
              </div>
            </div>
          </div>
        </GlassCard>

        {/* Play/Pause control */}
        <button
          onClick={togglePlayPause}
          className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-10 h-10 rounded-full bg-af-card border border-af-card-border flex items-center justify-center hover:bg-af-card-hover transition-colors shadow-lg"
        >
          {isPlaying ? (
            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
            </svg>
          ) : (
            <svg className="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z"/>
            </svg>
          )}
        </button>
      </div>

      {/* Steps List */}
      <div className="order-1 lg:order-2">
        <div className="space-y-3">
          {demoSteps.map((step, index) => (
            <button
              key={step.id}
              onClick={() => goToStep(index)}
              className={`w-full text-left p-4 sm:p-5 rounded-xl transition-all ${
                activeStep === index
                  ? 'bg-af-purple/20 border border-af-purple/40 shadow-lg shadow-af-purple/10'
                  : 'bg-af-card/30 border border-transparent hover:bg-af-card/50'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 transition-colors ${
                  activeStep === index
                    ? 'bg-af-purple text-white'
                    : activeStep > index
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-af-card-border text-white/60'
                }`}>
                  {activeStep > index ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.id
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className={`font-semibold mb-1 transition-colors ${
                    activeStep === index ? 'text-white' : 'text-white/80'
                  }`}>
                    {step.title}
                  </h3>
                  <p className={`text-sm transition-colors ${
                    activeStep === index ? 'text-white/70' : 'text-white/50'
                  }`}>
                    {step.description}
                  </p>

                  {/* Progress bar for active step */}
                  {activeStep === index && isPlaying && (
                    <div className="mt-3 h-1 bg-af-card rounded-full overflow-hidden">
                      <div
                        className="h-full bg-af-purple rounded-full transition-all duration-100"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* CTA after demo */}
        <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-af-purple/20 to-af-accent/10 border border-af-purple/20">
          <p className="text-white/80 text-sm mb-3">Ready to create your first audiobook?</p>
          <a
            href="/signup"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-af-purple text-white font-medium hover:bg-af-purple/90 transition-colors"
          >
            Start Free Trial
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </div>
      </div>
    </div>
  )
}

export default InteractiveDemo

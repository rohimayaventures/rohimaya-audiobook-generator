'use client'

import { useState } from 'react'
import { GlassCard } from '@/components/ui'

interface TutorialStep {
  id: string
  title: string
  content: string
  tips: string[]
  icon: React.ReactNode
}

const tutorialSteps: TutorialStep[] = [
  {
    id: 'prepare',
    title: 'Prepare Your Manuscript',
    content: 'Before uploading, make sure your manuscript is properly formatted. Clean formatting leads to better audiobook quality.',
    tips: [
      'Use clear chapter headings (Chapter 1, Chapter 2, etc.)',
      'Remove any headers, footers, and page numbers',
      'Ensure dialogue is properly punctuated with quotation marks',
      'Check for spelling and grammar errors',
      'Save as .docx, .pdf, .txt, or .epub format',
    ],
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    id: 'upload',
    title: 'Upload Your File',
    content: 'Upload your manuscript using our simple drag-and-drop interface or import directly from Google Drive.',
    tips: [
      'Drag and drop your file onto the upload area',
      'Or click to browse your computer',
      'Connect Google Drive for seamless imports',
      'Maximum file size: 50MB',
      'We support manuscripts up to 500,000 words',
    ],
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
    ),
  },
  {
    id: 'voices',
    title: 'Choose Your Voices',
    content: 'Select from our library of premium AI voices. For fiction, assign different voices to different characters.',
    tips: [
      'Preview each voice before selecting',
      'Match voice characteristics to your content type',
      'Use multi-voice for dialogue-heavy books',
      'Consider audiobook genre when selecting tone',
      'You can change voices anytime before generation',
    ],
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    ),
  },
  {
    id: 'customize',
    title: 'Customize Settings',
    content: 'Fine-tune your audiobook settings including speed, format, and chapter organization.',
    tips: [
      'Adjust narration speed (0.75x - 1.5x)',
      'Choose output format: MP3, WAV, or M4B',
      'Enable chapter markers for easy navigation',
      'Set audio quality (128kbps - 320kbps)',
      'Preview chapters before full generation',
    ],
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    id: 'generate',
    title: 'Generate & Download',
    content: 'Click generate and let our AI create your audiobook. Download in your preferred format when ready.',
    tips: [
      'Generation time depends on manuscript length',
      'You\'ll receive an email when it\'s ready',
      'Download individual chapters or full audiobook',
      'Files are stored for 30 days',
      'Re-generate anytime with different settings',
    ],
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
    ),
  },
]

export function TutorialSection() {
  const [activeStep, setActiveStep] = useState<string>('prepare')
  const currentStep = tutorialSteps.find(s => s.id === activeStep) || tutorialSteps[0]
  const currentIndex = tutorialSteps.findIndex(s => s.id === activeStep)

  return (
    <div className="max-w-6xl mx-auto">
      {/* Section Header */}
      <div className="text-center mb-12">
        <span className="inline-block px-4 py-1.5 rounded-full bg-af-purple/20 text-af-lavender text-sm font-medium mb-4">
          Step-by-Step Guide
        </span>
        <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
          How to Create Your Audiobook
        </h2>
        <p className="text-white/60 max-w-2xl mx-auto">
          Follow these simple steps to transform your manuscript into a professional audiobook.
          No technical expertise required.
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Steps Navigation */}
        <div className="lg:col-span-1">
          <div className="space-y-2">
            {tutorialSteps.map((step, index) => (
              <button
                key={step.id}
                onClick={() => setActiveStep(step.id)}
                className={`w-full flex items-center gap-4 p-4 rounded-xl text-left transition-all ${
                  activeStep === step.id
                    ? 'bg-af-purple/20 border border-af-purple/40'
                    : 'bg-af-card/30 border border-transparent hover:bg-af-card/50'
                }`}
              >
                <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                  activeStep === step.id
                    ? 'bg-af-purple text-white'
                    : 'bg-af-card text-white/60'
                }`}>
                  {index + 1}
                </div>
                <span className={`font-medium ${
                  activeStep === step.id ? 'text-white' : 'text-white/70'
                }`}>
                  {step.title}
                </span>
              </button>
            ))}
          </div>

          {/* Progress indicator */}
          <div className="mt-6 px-4">
            <div className="h-2 bg-af-card rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-af-purple to-af-accent rounded-full transition-all duration-300"
                style={{ width: `${((currentIndex + 1) / tutorialSteps.length) * 100}%` }}
              />
            </div>
            <p className="text-white/50 text-sm mt-2 text-center">
              Step {currentIndex + 1} of {tutorialSteps.length}
            </p>
          </div>
        </div>

        {/* Step Content */}
        <div className="lg:col-span-2">
          <GlassCard className="p-6 sm:p-8">
            {/* Step Header */}
            <div className="flex items-center gap-4 mb-6">
              <div className="w-14 h-14 rounded-2xl bg-af-purple/20 flex items-center justify-center text-af-lavender">
                {currentStep.icon}
              </div>
              <div>
                <p className="text-af-lavender text-sm font-medium">Step {currentIndex + 1}</p>
                <h3 className="text-xl sm:text-2xl font-bold text-white">{currentStep.title}</h3>
              </div>
            </div>

            {/* Step Description */}
            <p className="text-white/70 text-lg mb-8">
              {currentStep.content}
            </p>

            {/* Tips List */}
            <div className="bg-af-card/50 rounded-xl p-5">
              <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-af-lavender" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Tips for this step
              </h4>
              <ul className="space-y-3">
                {currentStep.tips.map((tip, index) => (
                  <li key={index} className="flex items-start gap-3 text-white/70">
                    <svg className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>

            {/* Navigation buttons */}
            <div className="flex justify-between mt-8">
              <button
                onClick={() => {
                  const prevIndex = currentIndex - 1
                  if (prevIndex >= 0) setActiveStep(tutorialSteps[prevIndex].id)
                }}
                disabled={currentIndex === 0}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  currentIndex === 0
                    ? 'text-white/30 cursor-not-allowed'
                    : 'text-white/70 hover:text-white hover:bg-af-card'
                }`}
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Previous
              </button>

              {currentIndex < tutorialSteps.length - 1 ? (
                <button
                  onClick={() => {
                    const nextIndex = currentIndex + 1
                    if (nextIndex < tutorialSteps.length) setActiveStep(tutorialSteps[nextIndex].id)
                  }}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-af-purple text-white font-medium hover:bg-af-purple/90 transition-colors"
                >
                  Next Step
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              ) : (
                <a
                  href="/signup"
                  className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-af-purple text-white font-medium hover:bg-af-purple/90 transition-colors"
                >
                  Get Started Now
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </a>
              )}
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  )
}

export default TutorialSection

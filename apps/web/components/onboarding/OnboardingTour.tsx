'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import dynamic from 'next/dynamic'
import type { Step, CallBackProps } from '@adi-prasetyo/react-joyride'
import { STATUS } from '@adi-prasetyo/react-joyride'

// Dynamic import to avoid SSR issues with react-joyride
const Joyride = dynamic(() => import('@adi-prasetyo/react-joyride'), { ssr: false })

// ============================================================================
// TOUR STEP DEFINITIONS
// ============================================================================

const DASHBOARD_TOUR_STEPS: Step[] = [
  {
    target: 'body',
    content: (
      <div className="text-center">
        <h3 className="text-lg font-bold text-white mb-2">Welcome to AuthorFlow Studios!</h3>
        <p className="text-white/80">
          Let us show you around. This quick tour will help you create your first audiobook in minutes.
        </p>
      </div>
    ),
    placement: 'center',
    disableBeacon: true,
    disableScrolling: true,
  },
  {
    target: '[data-tour="upload-section"]',
    content: (
      <div>
        <h3 className="font-bold text-white mb-2">1. Upload Your Manuscript</h3>
        <p className="text-white/80">
          Drag and drop your manuscript file here, or click to browse.
          We support DOCX, PDF, TXT, and more!
        </p>
      </div>
    ),
    placement: 'right',
    disableBeacon: true,
    spotlightPadding: 10,
  },
  {
    target: '[data-tour="voice-selection"]',
    content: (
      <div>
        <h3 className="font-bold text-white mb-2">2. Choose Your Narrator</h3>
        <p className="text-white/80">
          Select from 25+ premium AI narrators. Each has a unique style perfect for different genres.
          Click the play button to preview any voice!
        </p>
      </div>
    ),
    placement: 'left',
    disableBeacon: true,
    spotlightPadding: 10,
  },
  {
    target: '[data-tour="language-options"]',
    content: (
      <div>
        <h3 className="font-bold text-white mb-2">3. Multilingual Support</h3>
        <p className="text-white/80">
          Choose your input language or let us auto-detect. You can even translate your audiobook
          to a different language!
        </p>
      </div>
    ),
    placement: 'top',
    disableBeacon: true,
    spotlightPadding: 10,
  },
  {
    target: '[data-tour="create-button"]',
    content: (
      <div>
        <h3 className="font-bold text-white mb-2">4. Create Your Audiobook</h3>
        <p className="text-white/80">
          Once you&apos;re ready, click this button to start the magic. You&apos;ll be able to review
          and reorder chapters before we generate the audio.
        </p>
      </div>
    ),
    placement: 'top',
    disableBeacon: true,
    spotlightPadding: 10,
  },
  {
    target: '[data-tour="recent-jobs"]',
    content: (
      <div>
        <h3 className="font-bold text-white mb-2">5. Track Your Progress</h3>
        <p className="text-white/80">
          Your audiobooks will appear here. Click on any job to view details, download files,
          or retry if something went wrong.
        </p>
      </div>
    ),
    placement: 'top',
    disableBeacon: true,
    spotlightPadding: 10,
  },
  {
    target: 'body',
    content: (
      <div className="text-center">
        <h3 className="text-lg font-bold text-white mb-2">You&apos;re All Set!</h3>
        <p className="text-white/80 mb-4">
          That&apos;s everything you need to know. Ready to create your first audiobook?
        </p>
        <p className="text-sm text-white/60">
          Tip: You can always access help by hovering over the (?) icons.
        </p>
      </div>
    ),
    placement: 'center',
    disableBeacon: true,
    disableScrolling: true,
  },
]

const JOB_DETAIL_TOUR_STEPS: Step[] = [
  {
    target: '[data-tour="chapter-review"]',
    content: (
      <div>
        <h3 className="font-bold text-white mb-2">Review Your Chapters</h3>
        <p className="text-white/80">
          We&apos;ve detected the chapters in your manuscript. You can reorder them, change their type
          (Front Matter, Chapter, Back Matter), or exclude any you don&apos;t want.
        </p>
      </div>
    ),
    placement: 'top',
    disableBeacon: true,
  },
  {
    target: '[data-tour="chapter-drag"]',
    content: (
      <div>
        <h3 className="font-bold text-white mb-2">Drag to Reorder</h3>
        <p className="text-white/80">
          Drag chapters up or down to change their order in the final audiobook.
        </p>
      </div>
    ),
    placement: 'right',
  },
  {
    target: '[data-tour="approve-button"]',
    content: (
      <div>
        <h3 className="font-bold text-white mb-2">Approve & Generate</h3>
        <p className="text-white/80">
          When you&apos;re happy with the chapter order, click this button to start audio generation.
          We&apos;ll email you when it&apos;s ready!
        </p>
      </div>
    ),
    placement: 'top',
  },
]

// ============================================================================
// STORAGE KEYS
// ============================================================================

const TOUR_COMPLETED_KEY = 'authorflow_tour_completed'
const TOUR_SKIPPED_KEY = 'authorflow_tour_skipped'

// ============================================================================
// CUSTOM STYLES
// ============================================================================

const joyrideStyles = {
  options: {
    primaryColor: '#a855f7', // af-purple
    backgroundColor: 'rgba(15, 10, 31, 0.98)', // af-dark with opacity
    textColor: '#ffffff',
    overlayColor: 'rgba(0, 0, 0, 0.75)',
    spotlightShadow: '0 0 30px rgba(168, 85, 247, 0.5)',
    beaconSize: 36,
    arrowColor: 'rgba(15, 10, 31, 0.98)',
    zIndex: 10000,
  },
  tooltip: {
    borderRadius: 16,
    padding: 24,
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(168, 85, 247, 0.2)',
  },
  tooltipContainer: {
    textAlign: 'left' as const,
  },
  tooltipContent: {
    padding: 0,
  },
  buttonNext: {
    backgroundColor: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
    background: '#a855f7',
    borderRadius: 8,
    padding: '10px 20px',
    fontSize: 14,
    fontWeight: 600,
  },
  buttonBack: {
    color: 'rgba(255, 255, 255, 0.6)',
    marginRight: 10,
  },
  buttonSkip: {
    color: 'rgba(255, 255, 255, 0.4)',
  },
  spotlight: {
    borderRadius: 12,
  },
}

// ============================================================================
// ONBOARDING TOUR COMPONENT
// ============================================================================

interface OnboardingTourProps {
  tourType?: 'dashboard' | 'job-detail'
  forceShow?: boolean
  onComplete?: () => void
  onSkip?: () => void
  /** Pass true if user is new (has no jobs). Tour only shows for new users. */
  isNewUser?: boolean
}

export function OnboardingTour({
  tourType = 'dashboard',
  forceShow = false,
  onComplete,
  onSkip,
  isNewUser = false,
}: OnboardingTourProps) {
  const [run, setRun] = useState(false)
  const [stepIndex, setStepIndex] = useState(0)
  const [mounted, setMounted] = useState(false)
  const [ready, setReady] = useState(false)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  // Get the appropriate steps based on tour type
  const steps = tourType === 'dashboard' ? DASHBOARD_TOUR_STEPS : JOB_DETAIL_TOUR_STEPS

  // Wait for DOM elements to be ready before starting tour
  useEffect(() => {
    setMounted(true)

    // Give the page time to render all elements
    const readyTimer = setTimeout(() => setReady(true), 500)
    return () => clearTimeout(readyTimer)
  }, [])

  // Check if tour should run
  useEffect(() => {
    if (!mounted || !ready) return

    // Check if user has already completed or skipped the tour
    if (typeof window !== 'undefined') {
      const completed = localStorage.getItem(TOUR_COMPLETED_KEY)
      const skipped = localStorage.getItem(TOUR_SKIPPED_KEY)

      if (forceShow) {
        // Force show immediately (for testing or manual trigger)
        timerRef.current = setTimeout(() => setRun(true), 300)
      } else if (!completed && !skipped && isNewUser) {
        // Only auto-start tour for NEW users who haven't seen it
        // Wait a bit longer to ensure all elements are rendered
        timerRef.current = setTimeout(() => setRun(true), 1000)
      }
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [forceShow, isNewUser, mounted, ready])

  // Handle tour callbacks
  const handleJoyrideCallback = useCallback((data: CallBackProps) => {
    const { status, action, index, type } = data

    // Update step index for controlled mode
    if (type === 'step:after') {
      setStepIndex(index + (action === 'prev' ? -1 : 1))
    }

    // Handle tour completion
    if (status === STATUS.FINISHED) {
      setRun(false)
      localStorage.setItem(TOUR_COMPLETED_KEY, 'true')
      onComplete?.()
    }

    // Handle tour skip
    if (status === STATUS.SKIPPED) {
      setRun(false)
      localStorage.setItem(TOUR_SKIPPED_KEY, 'true')
      onSkip?.()
    }
  }, [onComplete, onSkip])

  // Don't render on server
  if (!mounted) return null

  return (
    <Joyride
      steps={steps}
      run={run}
      stepIndex={stepIndex}
      continuous
      showProgress
      showSkipButton
      scrollToFirstStep
      spotlightClicks
      disableOverlayClose
      callback={handleJoyrideCallback}
      styles={joyrideStyles}
      locale={{
        back: 'Back',
        close: 'Close',
        last: 'Got it!',
        next: 'Next',
        skip: 'Skip tour',
      }}
    />
  )
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Reset the tour state (useful for testing or allowing users to retake the tour)
 */
export function resetTour(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOUR_COMPLETED_KEY)
    localStorage.removeItem(TOUR_SKIPPED_KEY)
  }
}

/**
 * Check if user has completed the onboarding tour
 */
export function hasTourCompleted(): boolean {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOUR_COMPLETED_KEY) === 'true'
  }
  return false
}

/**
 * Manually mark tour as completed
 */
export function markTourCompleted(): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOUR_COMPLETED_KEY, 'true')
  }
}

export default OnboardingTour

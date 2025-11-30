'use client'

/**
 * Job Detail Page
 *
 * Displays the audiobook generation workflow with a multi-step flow indicator:
 * 1. Upload & Parse - Initial manuscript upload and chapter parsing
 * 2. Review Chapters - User reviews, reorders, and approves chapters
 * 3. Generate Audio - TTS processing for each chapter
 * 4. Export & Download - Final tracks ready for download
 *
 * Visual primitives used:
 * - GlassCard: Main container cards
 * - PrimaryButton/SecondaryButton: Actions
 * - Status badges with color coding
 * - Step indicator with completion states
 */

import { useState, useEffect, useCallback } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { GlassCard, PrimaryButton, SecondaryButton } from '@/components/ui'
import { Navbar, Footer, PageShell, AuthWrapper } from '@/components/layout'
import { ChapterReview, RetailSampleReview } from '@/components/chapters'
import { TracksView } from '@/components/tracks'
import { getCurrentUser } from '@/lib/supabaseClient'
import { getJob, getJobDownloadUrl, cancelJob, retryJob, getRetailSamples, type Job, type RetailSample } from '@/lib/apiClient'
import { signOut } from '@/lib/auth'

// Step definitions for the workflow
const WORKFLOW_STEPS = [
  { id: 'upload', label: 'Upload & Parse', icon: '📄' },
  { id: 'review', label: 'Review Chapters', icon: '📋' },
  { id: 'generate', label: 'Generate Audio', icon: '🎙️' },
  { id: 'export', label: 'Export & Download', icon: '📦' },
] as const

// Map job status to current step
const getStepFromStatus = (status: string): number => {
  switch (status) {
    case 'pending':
    case 'parsing':
      return 0 // Upload & Parse
    case 'chapters_pending':
      return 1 // Review Chapters
    case 'chapters_approved':
    case 'processing':
      return 2 // Generate Audio
    case 'completed':
      return 3 // Export & Download
    case 'failed':
    case 'cancelled':
      return -1 // Error state
    default:
      return 0
  }
}

// Step indicator component
function StepIndicator({ currentStep, status }: { currentStep: number; status: string }) {
  const isError = status === 'failed' || status === 'cancelled'

  return (
    <div className="flex items-center justify-between mb-8">
      {WORKFLOW_STEPS.map((step, index) => {
        const isCompleted = index < currentStep
        const isCurrent = index === currentStep
        const isPending = index > currentStep

        return (
          <div key={step.id} className="flex items-center flex-1">
            {/* Step circle */}
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-10 h-10 rounded-full flex items-center justify-center text-lg
                  transition-all duration-300
                  ${isCompleted
                    ? 'bg-green-500/20 border-2 border-green-500/50 text-green-400'
                    : isCurrent && !isError
                      ? 'bg-af-purple/20 border-2 border-af-purple animate-pulse text-white'
                      : isCurrent && isError
                        ? 'bg-red-500/20 border-2 border-red-500/50 text-red-400'
                        : 'bg-white/5 border-2 border-white/10 text-white/30'
                  }
                `}
              >
                {isCompleted ? '✓' : step.icon}
              </div>
              <span
                className={`
                  mt-2 text-xs font-medium text-center
                  ${isCompleted
                    ? 'text-green-400'
                    : isCurrent
                      ? isError ? 'text-red-400' : 'text-white'
                      : 'text-white/40'
                  }
                `}
              >
                {step.label}
              </span>
            </div>

            {/* Connector line */}
            {index < WORKFLOW_STEPS.length - 1 && (
              <div
                className={`
                  flex-1 h-0.5 mx-3 transition-all duration-500
                  ${isCompleted
                    ? 'bg-gradient-to-r from-green-500/50 to-green-500/50'
                    : isCurrent && !isError
                      ? 'bg-gradient-to-r from-af-purple/50 to-white/10'
                      : 'bg-white/10'
                  }
                `}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

// Helper to get friendly voice quality name
const getVoiceQualityName = (provider: string) => {
  switch (provider) {
    case 'openai':
      return 'Standard'
    case 'elevenlabs':
      return 'Premium'
    case 'google':
      return 'Gemini'
    default:
      return provider
  }
}

// Helper to get friendly voice name
const getVoiceName = (voiceId: string) => {
  const voiceNames: Record<string, string> = {
    // OpenAI voices
    'alloy': 'Alloy',
    'ash': 'Ash',
    'ballad': 'Ballad',
    'coral': 'Coral',
    'echo': 'Echo',
    'fable': 'Fable',
    'onyx': 'Onyx',
    'nova': 'Nova',
    'sage': 'Sage',
    'shimmer': 'Shimmer',
    'verse': 'Verse',
    // ElevenLabs voices (for future use)
    '21m00Tcm4TlvDq8ikWAM': 'Rachel',
    'EXAVITQu4vr4xnSDxMaL': 'Bella',
    'ErXwobaYiN019PkySvjV': 'Antoni',
    'TxGEqnHWrfWFTfGW9XjX': 'Josh',
  }
  return voiceNames[voiceId] || voiceId
}

function JobDetailContent() {
  const router = useRouter()
  const params = useParams()
  const jobId = params.id as string

  const [user, setUser] = useState<{ email?: string } | null>(null)
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [cancelling, setCancelling] = useState(false)
  const [retrying, setRetrying] = useState(false)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [retailSamples, setRetailSamples] = useState<RetailSample[]>([])
  const [isPolling, setIsPolling] = useState(false)

  // Fetch retail samples for completed jobs
  const fetchRetailSamples = useCallback(async () => {
    try {
      const samples = await getRetailSamples(jobId)
      setRetailSamples(samples)
    } catch (err) {
      console.error('Failed to fetch retail samples:', err)
    }
  }, [jobId])

  // Main data fetch
  const fetchData = useCallback(async () => {
    try {
      const jobData = await getJob(jobId)
      setJob(jobData)

      // Fetch audio URL if job is completed
      if (jobData.status === 'completed' && jobData.audio_path) {
        try {
          const { url } = await getJobDownloadUrl(jobId)
          setAudioUrl(url)
        } catch (err) {
          console.error('Failed to get audio URL:', err)
        }
      }

      // Fetch retail samples for completed or chapters_approved jobs
      if (jobData.status === 'completed' || jobData.status === 'chapters_approved') {
        fetchRetailSamples()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load job')
    }
    setLoading(false)
  }, [jobId, fetchRetailSamples])

  useEffect(() => {
    const initData = async () => {
      const currentUser = await getCurrentUser()
      setUser(currentUser)
      await fetchData()
    }
    initData()
  }, [fetchData])

  // Polling effect for processing states
  useEffect(() => {
    const shouldPoll = job?.status === 'processing' ||
                       job?.status === 'pending' ||
                       job?.status === 'parsing' ||
                       job?.status === 'chapters_approved'

    if (!shouldPoll) {
      setIsPolling(false)
      return
    }

    setIsPolling(true)
    const interval = setInterval(async () => {
      try {
        const jobData = await getJob(jobId)
        setJob(jobData)

        // Fetch audio URL when job completes
        if (jobData.status === 'completed' && jobData.audio_path && !audioUrl) {
          try {
            const { url } = await getJobDownloadUrl(jobId)
            setAudioUrl(url)
          } catch (err) {
            console.error('Failed to get audio URL:', err)
          }
          // Also fetch retail samples
          fetchRetailSamples()
        }
      } catch (err) {
        // Ignore polling errors
      }
    }, 5000)

    return () => {
      clearInterval(interval)
      setIsPolling(false)
    }
  }, [jobId, job?.status, audioUrl, fetchRetailSamples])

  const handleLogout = async () => {
    await signOut()
    router.push('/')
  }

  const handleCancel = async () => {
    if (!job) return

    setCancelling(true)
    try {
      await cancelJob(job.id)
      const jobData = await getJob(jobId)
      setJob(jobData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel job')
    }
    setCancelling(false)
  }

  const handleRetry = async () => {
    if (!job) return

    setRetrying(true)
    setError('')
    try {
      const updatedJob = await retryJob(job.id)
      setJob(updatedJob)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retry job')
    }
    setRetrying(false)
  }

  // Handle retail sample confirmed
  const handleRetailSampleConfirmed = (sample: RetailSample) => {
    setRetailSamples(prev => prev.map(s =>
      s.id === sample.id ? sample : { ...s, is_final: false }
    ))
  }

  // Format date
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // Status badge colors
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'processing':
      case 'parsing':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'chapters_pending':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      case 'chapters_approved':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
      case 'failed':
        return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'cancelled':
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
      default:
        return 'bg-white/10 text-white/60 border-white/10'
    }
  }

  // Status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✓'
      case 'processing':
      case 'parsing':
        return '⏳'
      case 'chapters_pending':
        return '📋'
      case 'chapters_approved':
        return '✅'
      case 'failed':
        return '✗'
      case 'cancelled':
        return '⊘'
      default:
        return '○'
    }
  }

  // Status text
  const getStatusText = (status: string) => {
    switch (status) {
      case 'chapters_pending':
        return 'Review Chapters'
      case 'chapters_approved':
        return 'Generating Audio'
      case 'parsing':
        return 'Parsing Manuscript'
      case 'processing':
        return 'Processing'
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
      case 'cancelled':
        return 'Cancelled'
      default:
        return status
    }
  }

  const currentStep = job ? getStepFromStatus(job.status) : 0
  const hasConfirmedRetailSample = retailSamples.some(s => s.is_final)

  return (
    <>
      <Navbar user={user} onLogout={handleLogout} />

      <PageShell>
        {/* Back link */}
        <Link
          href="/library"
          className="inline-flex items-center gap-2 text-white/60 hover:text-white transition-colors mb-6"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Library
        </Link>

        {loading ? (
          <GlassCard className="animate-pulse">
            <div className="h-8 bg-white/10 rounded w-1/2 mb-4" />
            <div className="h-4 bg-white/5 rounded w-1/3 mb-8" />
            <div className="h-32 bg-white/5 rounded" />
          </GlassCard>
        ) : error ? (
          <GlassCard className="text-center py-12">
            <div className="text-4xl mb-4">😕</div>
            <h3 className="text-xl font-semibold text-white mb-2">Error loading job</h3>
            <p className="text-red-400 mb-6">{error}</p>
            <SecondaryButton href="/library">Back to Library</SecondaryButton>
          </GlassCard>
        ) : job ? (
          <div className="space-y-6">
            {/* Header with Step Indicator */}
            <GlassCard>
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 mb-6">
                {/* Title and metadata */}
                <div>
                  <h1 className="text-2xl font-bold text-white mb-2">
                    {job.title || 'Untitled'}
                  </h1>
                  <p className="text-white/60">
                    Created {formatDate(job.created_at)}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  {/* Polling indicator */}
                  {isPolling && (
                    <div className="flex items-center gap-2 text-white/40 text-sm">
                      <span className="w-2 h-2 bg-af-purple rounded-full animate-pulse" />
                      Updating...
                    </div>
                  )}

                  <div
                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border ${getStatusColor(
                      job.status
                    )}`}
                  >
                    <span>{getStatusIcon(job.status)}</span>
                    <span className="font-medium">{getStatusText(job.status)}</span>
                  </div>
                </div>
              </div>

              {/* Step Indicator */}
              <StepIndicator currentStep={currentStep} status={job.status} />
            </GlassCard>

            {/* Chapter Review - Show when chapters are ready for review */}
            {job.status === 'chapters_pending' && (
              <ChapterReview
                job={job}
                onApproved={(updatedJob) => setJob(updatedJob)}
              />
            )}

            {/* Progress / Status */}
            {(job.status === 'processing' || job.status === 'pending' || job.status === 'parsing' || job.status === 'chapters_approved') && (
              <GlassCard>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white">
                    {job.status === 'parsing' ? 'Parsing Manuscript' : 'Generating Audio'}
                  </h2>
                  {isPolling && (
                    <span className="text-xs text-white/40">Auto-refreshing every 5s</span>
                  )}
                </div>

                <div className="mb-4">
                  <div className="flex justify-between text-sm text-white/60 mb-2">
                    <span>
                      {job.status === 'parsing'
                        ? 'Detecting chapters and structure...'
                        : job.status === 'chapters_approved'
                          ? 'Preparing audio generation...'
                          : 'Converting text to speech...'}
                    </span>
                    <span>{job.progress_percent || 0}%</span>
                  </div>
                  <div className="h-2 bg-af-card rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-af-purple to-af-pink transition-all duration-500"
                      style={{ width: `${job.progress_percent || 0}%` }}
                    />
                  </div>
                </div>

                <p className="text-white/40 text-sm">
                  {job.status === 'parsing'
                    ? 'We\'re analyzing your manuscript to detect chapters, front matter, and back matter.'
                    : 'This may take a few minutes depending on the length of your audiobook.'}
                </p>

                {job.status === 'processing' && (
                  <SecondaryButton
                    onClick={handleCancel}
                    disabled={cancelling}
                    className="mt-4"
                    size="sm"
                  >
                    {cancelling ? 'Cancelling...' : 'Cancel job'}
                  </SecondaryButton>
                )}
              </GlassCard>
            )}

            {/* Error */}
            {job.status === 'failed' && (
              <GlassCard>
                <h2 className="text-lg font-semibold text-red-400 mb-4">Generation Failed</h2>
                {job.error_message && (
                  <p className="text-white/80 bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-4">
                    {job.error_message}
                  </p>
                )}
                {job.retry_count && job.retry_count > 0 && (
                  <p className="text-white/40 text-sm mb-4">
                    This job has been retried {job.retry_count} time{job.retry_count > 1 ? 's' : ''}
                  </p>
                )}
                <div className="flex gap-4">
                  <PrimaryButton
                    onClick={handleRetry}
                    disabled={retrying}
                  >
                    {retrying ? 'Retrying...' : 'Retry this job'}
                  </PrimaryButton>
                  <SecondaryButton href="/dashboard">
                    Create new job
                  </SecondaryButton>
                </div>
              </GlassCard>
            )}

            {/* Cancelled */}
            {job.status === 'cancelled' && (
              <GlassCard>
                <h2 className="text-lg font-semibold text-gray-400 mb-4">Job Cancelled</h2>
                <p className="text-white/60 mb-4">
                  This job was cancelled before completion.
                </p>
                <div className="flex gap-4">
                  <PrimaryButton href="/dashboard">
                    Create New Audiobook
                  </PrimaryButton>
                  <SecondaryButton href="/library">
                    Back to Library
                  </SecondaryButton>
                </div>
              </GlassCard>
            )}

            {/* Completed State - Retail Sample + Tracks */}
            {job.status === 'completed' && (
              <>
                {/* Retail Sample Review - Show if we have samples and none confirmed yet */}
                {retailSamples.length > 0 && !hasConfirmedRetailSample && (
                  <RetailSampleReview
                    job={job}
                    onConfirmed={handleRetailSampleConfirmed}
                    onSkip={() => {}}
                  />
                )}

                {/* Retail Sample Confirmed Banner */}
                {hasConfirmedRetailSample && (
                  <GlassCard className="bg-green-500/5 border-green-500/20">
                    <div className="flex items-start gap-3">
                      <div className="text-green-400 mt-0.5">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="text-green-400 font-medium mb-1">Retail Sample Confirmed</h3>
                        <p className="text-white/60 text-sm">
                          Your retail sample has been selected and is included in the audio tracks.
                        </p>
                      </div>
                    </div>
                  </GlassCard>
                )}

                {/* Audio Tracks & Downloads */}
                <TracksView job={job} />
              </>
            )}

            {/* Legacy Audio Player (fallback when no tracks available) */}
            {job.status === 'completed' && audioUrl && (
              <GlassCard>
                <h2 className="text-lg font-semibold text-white mb-4">Quick Listen</h2>
                <audio
                  controls
                  className="w-full"
                  src={audioUrl}
                >
                  Your browser does not support the audio element.
                </audio>
              </GlassCard>
            )}

            {/* Job Details */}
            <GlassCard>
              <h2 className="text-lg font-semibold text-white mb-4">Job Details</h2>

              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {job.tts_provider && (
                  <div>
                    <dt className="text-white/40 text-sm">Voice Quality</dt>
                    <dd className="text-white">
                      {getVoiceQualityName(job.tts_provider)}
                    </dd>
                  </div>
                )}

                {job.narrator_voice_id && (
                  <div>
                    <dt className="text-white/40 text-sm">Narrator Voice</dt>
                    <dd className="text-white">{getVoiceName(job.narrator_voice_id)}</dd>
                  </div>
                )}

                {job.audio_format && (
                  <div>
                    <dt className="text-white/40 text-sm">Audio Format</dt>
                    <dd className="text-white uppercase">{job.audio_format}</dd>
                  </div>
                )}

                {job.input_language_code && (
                  <div>
                    <dt className="text-white/40 text-sm">Input Language</dt>
                    <dd className="text-white">{job.input_language_code}</dd>
                  </div>
                )}

                {job.output_language_code && (
                  <div>
                    <dt className="text-white/40 text-sm">Output Language</dt>
                    <dd className="text-white">{job.output_language_code}</dd>
                  </div>
                )}

                <div>
                  <dt className="text-white/40 text-sm">Created</dt>
                  <dd className="text-white">{formatDate(job.created_at)}</dd>
                </div>

                {job.completed_at && (
                  <div>
                    <dt className="text-white/40 text-sm">Completed</dt>
                    <dd className="text-white">{formatDate(job.completed_at)}</dd>
                  </div>
                )}
              </dl>
            </GlassCard>
          </div>
        ) : null}
      </PageShell>

      <Footer user={user} />
    </>
  )
}

export default function JobDetailPage() {
  return (
    <AuthWrapper>
      <JobDetailContent />
    </AuthWrapper>
  )
}

'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { GlassCard, PrimaryButton, SecondaryButton } from '@/components/ui'
import { Navbar, Footer, PageShell, AuthWrapper } from '@/components/layout'
import { getCurrentUser } from '@/lib/supabaseClient'
import { getJob, getDownloadUrl, cancelJob, retryJob, type Job } from '@/lib/apiClient'
import { signOut } from '@/lib/auth'

// Helper to get friendly voice quality name
const getVoiceQualityName = (provider: string) => {
  switch (provider) {
    case 'openai':
      return 'Standard'
    case 'elevenlabs':
      return 'Premium'
    default:
      return provider
  }
}

// Helper to get friendly voice name
const getVoiceName = (voiceId: string) => {
  const voiceNames: Record<string, string> = {
    'alloy': 'Alloy',
    'echo': 'Echo',
    'fable': 'Fable',
    'onyx': 'Onyx',
    'nova': 'Nova',
    'shimmer': 'Shimmer',
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

  useEffect(() => {
    const fetchData = async () => {
      const currentUser = await getCurrentUser()
      setUser(currentUser)

      try {
        const jobData = await getJob(jobId)
        setJob(jobData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load job')
      }

      setLoading(false)
    }

    fetchData()

    // Poll for updates if job is processing
    const interval = setInterval(async () => {
      if (job?.status === 'processing' || job?.status === 'pending') {
        try {
          const jobData = await getJob(jobId)
          setJob(jobData)
        } catch (err) {
          // Ignore polling errors
        }
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [jobId, job?.status])

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
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'failed':
        return 'bg-red-500/20 text-red-400 border-red-500/30'
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
        return '⏳'
      case 'failed':
        return '✗'
      default:
        return '○'
    }
  }

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
            {/* Header */}
            <GlassCard>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-white mb-2">
                    {job.title || 'Untitled'}
                  </h1>
                  <p className="text-white/60">
                    Created {formatDate(job.created_at)}
                  </p>
                </div>

                <div
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border ${getStatusColor(
                    job.status
                  )}`}
                >
                  <span>{getStatusIcon(job.status)}</span>
                  <span className="font-medium capitalize">{job.status}</span>
                </div>
              </div>
            </GlassCard>

            {/* Progress / Status */}
            {(job.status === 'processing' || job.status === 'pending') && (
              <GlassCard>
                <h2 className="text-lg font-semibold text-white mb-4">Progress</h2>

                <div className="mb-4">
                  <div className="flex justify-between text-sm text-white/60 mb-2">
                    <span>Processing your audiobook...</span>
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
                  This may take a few minutes depending on the length of your manuscript.
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
                <h2 className="text-lg font-semibold text-red-400 mb-4">Error</h2>
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

            {/* Audio Player & Download */}
            {job.status === 'completed' && (
              <GlassCard>
                <h2 className="text-lg font-semibold text-white mb-4">Your Audiobook</h2>

                {job.audio_path ? (
                  <div className="space-y-4">
                    <audio
                      controls
                      className="w-full"
                      src={getDownloadUrl(job.id)}
                    >
                      Your browser does not support the audio element.
                    </audio>

                    <div className="flex gap-4">
                      <a
                        href={getDownloadUrl(job.id)}
                        download
                        className="flex-1"
                      >
                        <PrimaryButton className="w-full">
                          Download audiobook
                        </PrimaryButton>
                      </a>
                    </div>
                  </div>
                ) : (
                  <p className="text-white/60">Audio file is being prepared...</p>
                )}
              </GlassCard>
            )}

            {/* Job Details */}
            <GlassCard>
              <h2 className="text-lg font-semibold text-white mb-4">Details</h2>

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

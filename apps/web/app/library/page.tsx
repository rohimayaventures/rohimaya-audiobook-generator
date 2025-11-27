'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { GlassCard, PrimaryButton, SecondaryButton } from '@/components/ui'
import { Navbar, Footer, PageShell, AuthWrapper } from '@/components/layout'
import { getCurrentUser } from '@/lib/supabaseClient'
import { getJobs, getJobDownloadUrl, retryJob, type Job } from '@/lib/apiClient'
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

function LibraryContent() {
  const router = useRouter()
  const [user, setUser] = useState<{ email?: string } | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'completed' | 'processing' | 'failed'>('all')
  const [retrying, setRetrying] = useState<string | null>(null)
  const [downloadUrls, setDownloadUrls] = useState<Record<string, string>>({})
  const [downloading, setDownloading] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      const currentUser = await getCurrentUser()
      setUser(currentUser)

      try {
        const jobsList = await getJobs()
        setJobs(jobsList)

        // Pre-fetch download URLs for completed jobs
        const completedJobs = jobsList.filter(j => j.status === 'completed' && j.audio_path)
        const urlPromises = completedJobs.map(async (job) => {
          try {
            const { url } = await getJobDownloadUrl(job.id)
            return { id: job.id, url }
          } catch {
            return null
          }
        })
        const results = await Promise.all(urlPromises)
        const urls: Record<string, string> = {}
        results.forEach(r => {
          if (r) urls[r.id] = r.url
        })
        setDownloadUrls(urls)
      } catch (err) {
        console.error('Failed to fetch jobs:', err)
      }

      setLoading(false)
    }

    fetchData()
  }, [])

  const handleLogout = async () => {
    await signOut()
    router.push('/')
  }

  const handleRetry = async (jobId: string) => {
    setRetrying(jobId)
    try {
      const updatedJob = await retryJob(jobId)
      // Update job in local state
      setJobs(jobs.map(j => j.id === jobId ? updatedJob : j))
    } catch (err) {
      console.error('Failed to retry job:', err)
      alert(err instanceof Error ? err.message : 'Failed to retry job')
    } finally {
      setRetrying(null)
    }
  }

  const handleDownload = async (job: Job) => {
    // Check if we already have the URL cached
    if (downloadUrls[job.id]) {
      window.open(downloadUrls[job.id], '_blank')
      return
    }

    setDownloading(job.id)
    try {
      const { url } = await getJobDownloadUrl(job.id)
      // Cache the URL
      setDownloadUrls(prev => ({ ...prev, [job.id]: url }))
      // Trigger download
      window.open(url, '_blank')
    } catch (err) {
      console.error('Failed to get download URL:', err)
      alert(err instanceof Error ? err.message : 'Failed to get download URL')
    } finally {
      setDownloading(null)
    }
  }

  // Filter jobs
  const filteredJobs = jobs.filter((job) => {
    if (filter === 'all') return true
    return job.status === filter
  })

  // Format date
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  // Status badge colors
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 text-green-400'
      case 'processing':
        return 'bg-yellow-500/20 text-yellow-400'
      case 'failed':
        return 'bg-red-500/20 text-red-400'
      default:
        return 'bg-white/10 text-white/60'
    }
  }

  return (
    <>
      <Navbar user={user} onLogout={handleLogout} />

      <PageShell title="Library" subtitle="Your audiobook collection">
        {/* Filter tabs */}
        <div className="flex gap-2 mb-8 flex-wrap">
          {(['all', 'completed', 'processing', 'failed'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${
                filter === f
                  ? 'bg-af-purple text-white'
                  : 'bg-af-card text-white/60 hover:text-white'
              }`}
            >
              {f}
              {f !== 'all' && (
                <span className="ml-2 opacity-60">
                  ({jobs.filter((j) => j.status === f).length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Jobs grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="glass p-6 animate-pulse">
                <div className="h-5 bg-white/10 rounded w-3/4 mb-4" />
                <div className="h-4 bg-white/5 rounded w-1/2 mb-2" />
                <div className="h-4 bg-white/5 rounded w-1/3" />
              </div>
            ))}
          </div>
        ) : filteredJobs.length === 0 ? (
          <GlassCard className="text-center py-12">
            <div className="text-4xl mb-4">📚</div>
            <h3 className="text-xl font-semibold text-white mb-2">
              {filter === 'all' ? 'No audiobooks yet' : `No ${filter} audiobooks`}
            </h3>
            <p className="text-white/60 mb-6">
              {filter === 'all'
                ? 'Create your first audiobook to get started'
                : `You don't have any ${filter} audiobooks`}
            </p>
            <PrimaryButton href="/dashboard">Create audiobook</PrimaryButton>
          </GlassCard>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredJobs.map((job) => (
              <GlassCard key={job.id} variant="compact" glow>
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white truncate flex-1 mr-2">
                    {job.title || 'Untitled'}
                  </h3>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium shrink-0 ${getStatusColor(
                      job.status
                    )}`}
                  >
                    {job.status}
                  </span>
                </div>

                <div className="text-white/40 text-sm mb-4">
                  <p>Created {formatDate(job.created_at)}</p>
                  {job.tts_provider && job.narrator_voice_id && (
                    <p>{getVoiceQualityName(job.tts_provider)} · {getVoiceName(job.narrator_voice_id)}</p>
                  )}
                </div>

                {/* Audio player for completed jobs */}
                {job.status === 'completed' && job.audio_path && downloadUrls[job.id] && (
                  <audio
                    controls
                    className="w-full mb-4 h-10"
                    src={downloadUrls[job.id]}
                  >
                    Your browser does not support the audio element.
                  </audio>
                )}

                {/* Error message for failed jobs */}
                {job.status === 'failed' && job.error_message && (
                  <p className="text-red-400 text-sm mb-4 line-clamp-2">
                    {job.error_message}
                  </p>
                )}

                {/* Retry count badge */}
                {job.retry_count && job.retry_count > 0 && (
                  <p className="text-white/40 text-xs mb-2">
                    Retried {job.retry_count}x
                  </p>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  <SecondaryButton
                    href={`/job/${job.id}`}
                    className="flex-1"
                    size="sm"
                  >
                    View details
                  </SecondaryButton>

                  {job.status === 'completed' && (
                    <PrimaryButton
                      className="flex-1"
                      size="sm"
                      onClick={() => handleDownload(job)}
                      disabled={downloading === job.id}
                    >
                      {downloading === job.id ? 'Loading...' : 'Download'}
                    </PrimaryButton>
                  )}

                  {job.status === 'failed' && (
                    <PrimaryButton
                      className="flex-1"
                      size="sm"
                      onClick={() => handleRetry(job.id)}
                      disabled={retrying === job.id}
                    >
                      {retrying === job.id ? 'Retrying...' : 'Retry'}
                    </PrimaryButton>
                  )}
                </div>
              </GlassCard>
            ))}
          </div>
        )}
      </PageShell>

      <Footer user={user} />
    </>
  )
}

export default function LibraryPage() {
  return (
    <AuthWrapper>
      <LibraryContent />
    </AuthWrapper>
  )
}

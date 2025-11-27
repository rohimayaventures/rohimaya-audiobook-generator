'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useDropzone } from 'react-dropzone'
import { GlassCard, PrimaryButton } from '@/components/ui'
import { Navbar, Footer, PageShell, AuthWrapper } from '@/components/layout'
import { createClient, getCurrentUser } from '@/lib/supabaseClient'
import { createJob, getJobs, type Job } from '@/lib/apiClient'
import { signOut } from '@/lib/auth'
import { getBillingInfo, type BillingInfo, PLANS } from '@/lib/billing'

// Voice options (OpenAI TTS voices)
const VOICES = [
  { id: 'alloy', name: 'Alloy', description: 'Neutral, versatile - general narration', gender: 'neutral' },
  { id: 'ash', name: 'Ash', description: 'Warm, conversational - dialogue stories', gender: 'male' },
  { id: 'ballad', name: 'Ballad', description: 'Smooth, melodic - poetry & literary fiction', gender: 'male' },
  { id: 'coral', name: 'Coral', description: 'Clear, professional - non-fiction', gender: 'female' },
  { id: 'echo', name: 'Echo', description: 'Deep, resonant - thrillers & mysteries', gender: 'male' },
  { id: 'fable', name: 'Fable', description: 'Expressive storyteller - fantasy & children\'s', gender: 'female' },
  { id: 'onyx', name: 'Onyx', description: 'Deep, authoritative - business & history', gender: 'male' },
  { id: 'nova', name: 'Nova', description: 'Bright, energetic - self-help & motivation', gender: 'female' },
  { id: 'sage', name: 'Sage', description: 'Calm, wise - meditation & wellness', gender: 'female' },
  { id: 'shimmer', name: 'Shimmer', description: 'Soft, gentle - romance & drama', gender: 'female' },
  { id: 'verse', name: 'Verse', description: 'Dynamic, engaging - adventure & action', gender: 'male' },
]

// Output format options
const OUTPUT_FORMATS = [
  { id: 'mp3', name: 'MP3', description: 'Universal compatibility' },
  { id: 'wav', name: 'WAV', description: 'Lossless quality' },
  { id: 'flac', name: 'FLAC', description: 'High quality lossless' },
  { id: 'm4b', name: 'M4B', description: 'Audiobook format' },
]

interface UserWithMetadata {
  email?: string
  user_metadata?: {
    display_name?: string
  }
}

function DashboardContent() {
  const router = useRouter()
  const [user, setUser] = useState<UserWithMetadata | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [loadingJobs, setLoadingJobs] = useState(true)
  const [billingInfo, setBillingInfo] = useState<BillingInfo | null>(null)
  const [loadingBilling, setLoadingBilling] = useState(true)

  // Form state
  const [inputMode, setInputMode] = useState<'file' | 'text'>('file')
  const [file, setFile] = useState<File | null>(null)
  const [text, setText] = useState('')
  const [title, setTitle] = useState('')
  const [voiceId, setVoiceId] = useState('alloy')
  const [outputFormat, setOutputFormat] = useState('mp3')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')

  // Fetch user, jobs, and billing info on mount
  useEffect(() => {
    const fetchData = async () => {
      const currentUser = await getCurrentUser()
      setUser(currentUser)

      try {
        const jobsList = await getJobs({ limit: 5 })
        setJobs(jobsList)
      } catch (err) {
        console.error('Failed to fetch jobs:', err)
      }

      setLoadingJobs(false)

      // Fetch billing info
      try {
        const supabase = createClient()
        const { data: { session } } = await supabase.auth.getSession()
        if (session?.access_token) {
          const billing = await getBillingInfo(session.access_token)
          setBillingInfo(billing)
        }
      } catch (err) {
        console.error('Failed to fetch billing info:', err)
      }
      setLoadingBilling(false)
    }

    fetchData()
  }, [])

  // File dropzone
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
      if (!title) {
        // Set title from filename
        const name = acceptedFiles[0].name.replace(/\.[^/.]+$/, '')
        setTitle(name)
      }
    }
  }, [title])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
  })

  // Handle job creation
  const handleCreateJob = async () => {
    setCreateError('')

    if (inputMode === 'file' && !file) {
      setCreateError('Please select a file')
      return
    }

    if (inputMode === 'text' && !text.trim()) {
      setCreateError('Please enter some text')
      return
    }

    setCreating(true)

    try {
      const payload = {
        title: title || (file?.name.replace(/\.[^/.]+$/, '') || 'Untitled'),
        source_type: inputMode === 'file' ? 'upload' as const : 'paste' as const,
        mode: 'single_voice' as const,
        tts_provider: 'openai' as const,
        narrator_voice_id: voiceId,
        audio_format: outputFormat,
        audio_bitrate: '128k',
        ...(inputMode === 'text' ? { manuscript_text: text } : {}),
      }

      await createJob(payload, inputMode === 'file' ? file! : undefined)

      // Refresh jobs list
      const updatedJobs = await getJobs({ limit: 5 })
      setJobs(updatedJobs)

      // Reset form
      setFile(null)
      setText('')
      setTitle('')
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create job')
    }

    setCreating(false)
  }

  // Handle logout
  const handleLogout = async () => {
    await signOut()
    router.push('/')
  }

  // Format date
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
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

      <PageShell
        title={`Welcome back${user?.user_metadata?.display_name ? `, ${user.user_metadata.display_name}` : (user?.email ? `, ${user.email.split('@')[0]}` : '')}`}
        subtitle="Create and manage your audiobook projects"
      >
        {/* Plan Info Banner */}
        {!loadingBilling && billingInfo && (
          <div className="mb-8 p-4 rounded-xl bg-gradient-to-r from-af-purple/20 to-af-purple-soft/20 border border-af-purple/30">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                {/* Plan Badge */}
                <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
                  billingInfo.plan_id === 'free'
                    ? 'bg-white/10 text-white/80'
                    : billingInfo.plan_id === 'admin'
                    ? 'bg-purple-600 text-white'
                    : 'bg-af-purple text-white'
                }`}>
                  {billingInfo.plan_name || (PLANS[billingInfo.plan_id]?.name || 'Free')}
                </div>

                {/* Usage Info */}
                {billingInfo.plan_id !== 'admin' && billingInfo.entitlements && (
                  <div className="text-sm text-white/60">
                    {billingInfo.entitlements.max_projects_per_month === null ? (
                      <span>Unlimited projects</span>
                    ) : (
                      <span>
                        {billingInfo.usage?.projects_created || 0} / {billingInfo.entitlements.max_projects_per_month} projects this month
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Upgrade/Manage Button */}
              <div className="flex gap-3">
                {billingInfo.plan_id === 'free' ? (
                  <Link
                    href="/pricing"
                    className="px-4 py-2 rounded-lg bg-af-purple hover:bg-af-purple-soft text-white text-sm font-medium transition-colors"
                  >
                    Upgrade Plan
                  </Link>
                ) : billingInfo.plan_id !== 'admin' && (
                  <Link
                    href="/billing"
                    className="px-4 py-2 rounded-lg bg-af-card hover:bg-white/10 text-white/80 text-sm font-medium transition-colors"
                  >
                    Manage Billing
                  </Link>
                )}
              </div>
            </div>

            {/* Period End Warning */}
            {billingInfo.cancel_at_period_end && billingInfo.current_period_end && (
              <div className="mt-3 text-sm text-yellow-400">
                Your subscription will end on {new Date(billingInfo.current_period_end).toLocaleDateString()}
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Create New Audiobook */}
          <GlassCard title="Create a new audiobook">
            {/* Input mode toggle */}
            <div className="flex gap-2 mb-6">
              <button
                onClick={() => setInputMode('file')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  inputMode === 'file'
                    ? 'bg-af-purple text-white'
                    : 'bg-af-card text-white/60 hover:text-white'
                }`}
              >
                Upload file
              </button>
              <button
                onClick={() => setInputMode('text')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  inputMode === 'text'
                    ? 'bg-af-purple text-white'
                    : 'bg-af-card text-white/60 hover:text-white'
                }`}
              >
                Paste text
              </button>
            </div>

            {/* File dropzone */}
            {inputMode === 'file' && (
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-af-purple bg-af-purple/10'
                    : 'border-af-card-border hover:border-af-purple/50'
                }`}
              >
                <input {...getInputProps()} />
                {file ? (
                  <div>
                    <p className="text-white font-medium">{file.name}</p>
                    <p className="text-white/40 text-sm mt-1">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-white/60">
                      {isDragActive
                        ? 'Drop your file here...'
                        : 'Drag & drop your manuscript, or click to browse'}
                    </p>
                    <p className="text-white/40 text-sm mt-2">
                      Supports .txt, .md, .docx, .pdf
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Text input */}
            {inputMode === 'text' && (
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste your manuscript text here..."
                className="input-field min-h-[200px] resize-none"
              />
            )}

            {/* Title */}
            <div className="mt-4">
              <label className="block text-sm font-medium text-white/80 mb-2">
                Title (optional)
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="My Audiobook"
                className="input-field"
              />
            </div>

            {/* Narrator Voice */}
            <div className="mt-4">
              <label className="block text-sm font-medium text-white/80 mb-2">
                Narrator Voice
              </label>
              <select
                value={voiceId}
                onChange={(e) => setVoiceId(e.target.value)}
                className="input-field"
              >
                {VOICES.map((voice) => (
                  <option key={voice.id} value={voice.id}>
                    {voice.name} - {voice.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Audio Format */}
            <div className="mt-4">
              <label className="block text-sm font-medium text-white/80 mb-2">
                Audio Format
              </label>
              <select
                value={outputFormat}
                onChange={(e) => setOutputFormat(e.target.value)}
                className="input-field"
              >
                {OUTPUT_FORMATS.map((format) => (
                  <option key={format.id} value={format.id}>
                    {format.name} - {format.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Error message */}
            {createError && (
              <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {createError}
              </div>
            )}

            {/* Submit button */}
            <PrimaryButton
              onClick={handleCreateJob}
              loading={creating}
              disabled={creating}
              className="w-full mt-6"
            >
              Start conversion
            </PrimaryButton>
          </GlassCard>

          {/* Recent Jobs */}
          <GlassCard title="Recent jobs">
            {loadingJobs ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-white/10 rounded w-3/4 mb-2" />
                    <div className="h-3 bg-white/5 rounded w-1/2" />
                  </div>
                ))}
              </div>
            ) : jobs.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-white/40">No jobs yet</p>
                <p className="text-white/30 text-sm mt-1">
                  Create your first audiobook to get started
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {jobs.map((job) => (
                  <Link
                    key={job.id}
                    href={`/job/${job.id}`}
                    className="block p-4 rounded-lg bg-af-card hover:bg-white/10 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-white font-medium">
                          {job.title || 'Untitled'}
                        </p>
                        <p className="text-white/40 text-sm">
                          {formatDate(job.created_at)}
                        </p>
                      </div>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
                          job.status
                        )}`}
                      >
                        {job.status}
                      </span>
                    </div>
                  </Link>
                ))}

                <Link
                  href="/library"
                  className="block text-center text-af-purple-soft hover:text-white transition-colors text-sm py-2"
                >
                  View all jobs →
                </Link>
              </div>
            )}
          </GlassCard>
        </div>
      </PageShell>

      <Footer user={user} />
    </>
  )
}

export default function DashboardPage() {
  return (
    <AuthWrapper>
      <DashboardContent />
    </AuthWrapper>
  )
}

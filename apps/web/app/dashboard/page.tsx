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

// Voice profile options
const VOICE_PROFILES = [
  { id: 'warm-narrator', name: 'Warm Narrator', description: 'Friendly and engaging' },
  { id: 'dramatic', name: 'Dramatic', description: 'Expressive and theatrical' },
  { id: 'professional', name: 'Professional', description: 'Clear and authoritative' },
  { id: 'storyteller', name: 'Storyteller', description: 'Rich and immersive' },
]

// Output format options
const OUTPUT_FORMATS = [
  { id: 'mp3', name: 'MP3', description: 'Universal compatibility' },
  { id: 'wav', name: 'WAV', description: 'Lossless quality' },
  { id: 'm4b', name: 'M4B', description: 'Audiobook format' },
]

function DashboardContent() {
  const router = useRouter()
  const [user, setUser] = useState<{ email?: string } | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [loadingJobs, setLoadingJobs] = useState(true)

  // Form state
  const [inputMode, setInputMode] = useState<'file' | 'text'>('file')
  const [file, setFile] = useState<File | null>(null)
  const [text, setText] = useState('')
  const [title, setTitle] = useState('')
  const [voiceProfile, setVoiceProfile] = useState('warm-narrator')
  const [outputFormat, setOutputFormat] = useState('mp3')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')

  // Fetch user and jobs on mount
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
        voice_profile: voiceProfile,
        output_format: outputFormat,
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
        title={`Welcome back${user?.email ? `, ${user.email.split('@')[0]}` : ''}`}
        subtitle="Create and manage your audiobook projects"
      >
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
                      Supports .txt, .docx, .pdf
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

            {/* Voice Profile */}
            <div className="mt-4">
              <label className="block text-sm font-medium text-white/80 mb-2">
                Voice Profile
              </label>
              <select
                value={voiceProfile}
                onChange={(e) => setVoiceProfile(e.target.value)}
                className="input-field"
              >
                {VOICE_PROFILES.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.name} - {profile.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Output Format */}
            <div className="mt-4">
              <label className="block text-sm font-medium text-white/80 mb-2">
                Output Format
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
                          {job.title || job.filename || 'Untitled'}
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

      <Footer />
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

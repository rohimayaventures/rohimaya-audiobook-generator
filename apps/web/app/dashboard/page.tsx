'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useDropzone } from 'react-dropzone'
import { GlassCard, PrimaryButton } from '@/components/ui'
import { Navbar, Footer, PageShell, AuthWrapper } from '@/components/layout'
import { createClient, getCurrentUser } from '@/lib/supabaseClient'
import {
  createJob,
  getJobs,
  getGoogleDriveAuthUrl,
  getGoogleDriveStatus,
  listGoogleDriveFiles,
  importGoogleDriveFile,
  disconnectGoogleDrive,
  type Job,
  type GoogleDriveFile,
  type GoogleDriveStatus,
} from '@/lib/apiClient'
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

// Cover art vibe options
const COVER_VIBES = [
  { id: 'dramatic', name: 'Dramatic', description: 'Bold, cinematic style' },
  { id: 'minimalist', name: 'Minimalist', description: 'Clean, simple design' },
  { id: 'vintage', name: 'Vintage', description: 'Classic, retro feel' },
  { id: 'fantasy', name: 'Fantasy', description: 'Magical, ethereal style' },
  { id: 'modern', name: 'Modern', description: 'Contemporary, sleek design' },
  { id: 'literary', name: 'Literary', description: 'Elegant, bookish aesthetic' },
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
  const [inputMode, setInputMode] = useState<'file' | 'text' | 'google_drive'>('file')
  const [file, setFile] = useState<File | null>(null)
  const [text, setText] = useState('')
  const [title, setTitle] = useState('')
  const [voiceId, setVoiceId] = useState('alloy')
  const [outputFormat, setOutputFormat] = useState('mp3')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')

  // Cover art options
  const [generateCover, setGenerateCover] = useState(false)
  const [coverVibe, setCoverVibe] = useState('dramatic')

  // Google Drive state
  const [googleDriveStatus, setGoogleDriveStatus] = useState<GoogleDriveStatus | null>(null)
  const [googleDriveFiles, setGoogleDriveFiles] = useState<GoogleDriveFile[]>([])
  const [selectedDriveFile, setSelectedDriveFile] = useState<GoogleDriveFile | null>(null)
  const [loadingDriveFiles, setLoadingDriveFiles] = useState(false)
  const [driveImporting, setDriveImporting] = useState(false)
  const [importedManuscriptPath, setImportedManuscriptPath] = useState<string | null>(null)

  // Fetch user, jobs, billing info, and Google Drive status on mount
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

      // Fetch Google Drive status
      try {
        const driveStatus = await getGoogleDriveStatus()
        setGoogleDriveStatus(driveStatus)
      } catch (err) {
        console.error('Failed to fetch Google Drive status:', err)
      }
    }

    fetchData()
  }, [])

  // Fetch Google Drive files when mode changes to google_drive and user is connected
  useEffect(() => {
    if (inputMode === 'google_drive' && googleDriveStatus?.connected) {
      fetchDriveFiles()
    }
  }, [inputMode, googleDriveStatus?.connected])

  // Fetch Google Drive files
  const fetchDriveFiles = async () => {
    setLoadingDriveFiles(true)
    try {
      const response = await listGoogleDriveFiles({ pageSize: 20 })
      setGoogleDriveFiles(response.files)
    } catch (err) {
      console.error('Failed to fetch Drive files:', err)
      setCreateError('Failed to load Google Drive files')
    }
    setLoadingDriveFiles(false)
  }

  // Connect to Google Drive
  const handleConnectGoogleDrive = async () => {
    try {
      const { auth_url } = await getGoogleDriveAuthUrl()
      window.location.href = auth_url
    } catch (err) {
      console.error('Failed to get Google Drive auth URL:', err)
      setCreateError('Failed to connect to Google Drive')
    }
  }

  // Disconnect Google Drive
  const handleDisconnectGoogleDrive = async () => {
    try {
      await disconnectGoogleDrive()
      setGoogleDriveStatus({ connected: false, has_tokens: false, configured: googleDriveStatus?.configured || false })
      setGoogleDriveFiles([])
      setSelectedDriveFile(null)
    } catch (err) {
      console.error('Failed to disconnect Google Drive:', err)
    }
  }

  // Import selected file from Google Drive
  const handleImportDriveFile = async () => {
    if (!selectedDriveFile) return

    setDriveImporting(true)
    setCreateError('')

    try {
      const result = await importGoogleDriveFile(selectedDriveFile.id)
      setImportedManuscriptPath(result.manuscript_path)
      if (!title) {
        setTitle(result.filename.replace(/\.[^/.]+$/, ''))
      }
    } catch (err) {
      console.error('Failed to import Drive file:', err)
      setCreateError(err instanceof Error ? err.message : 'Failed to import file')
    }

    setDriveImporting(false)
  }

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

    if (inputMode === 'google_drive' && !importedManuscriptPath) {
      setCreateError('Please import a file from Google Drive first')
      return
    }

    setCreating(true)

    try {
      // Determine source type
      let sourceType: 'upload' | 'paste' | 'google_drive' = 'upload'
      if (inputMode === 'text') sourceType = 'paste'
      else if (inputMode === 'google_drive') sourceType = 'google_drive'

      const payload = {
        title: title || (file?.name.replace(/\.[^/.]+$/, '') || selectedDriveFile?.name.replace(/\.[^/.]+$/, '') || 'Untitled'),
        source_type: sourceType,
        mode: 'single_voice' as const,
        tts_provider: 'openai' as const,
        narrator_voice_id: voiceId,
        audio_format: outputFormat,
        audio_bitrate: '128k',
        // Text or Google Drive source path
        ...(inputMode === 'text' ? { manuscript_text: text } : {}),
        ...(inputMode === 'google_drive' && importedManuscriptPath ? { source_path: importedManuscriptPath } : {}),
        // Cover art options
        ...(generateCover ? { generate_cover: true, cover_vibe: coverVibe } : {}),
      }

      await createJob(payload, inputMode === 'file' ? file! : undefined)

      // Refresh jobs list
      const updatedJobs = await getJobs({ limit: 5 })
      setJobs(updatedJobs)

      // Reset form
      setFile(null)
      setText('')
      setTitle('')
      setSelectedDriveFile(null)
      setImportedManuscriptPath(null)
      setGenerateCover(false)
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

                {/* Trial Badge */}
                {billingInfo.trial?.is_trialing && (
                  <div className="px-3 py-1 rounded-full text-sm font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                    {billingInfo.trial.trial_days_remaining !== null && billingInfo.trial.trial_days_remaining > 0
                      ? `Trial: ${billingInfo.trial.trial_days_remaining} day${billingInfo.trial.trial_days_remaining !== 1 ? 's' : ''} left`
                      : 'Trial ending today'}
                  </div>
                )}

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
              {googleDriveStatus?.configured && (
                <button
                  onClick={() => setInputMode('google_drive')}
                  className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 ${
                    inputMode === 'google_drive'
                      ? 'bg-af-purple text-white'
                      : 'bg-af-card text-white/60 hover:text-white'
                  }`}
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7.71 3.5L1.15 15l3.43 6h13.16l3.42-6L14.57 3.5H7.71zm-.78 1h6.21L17.7 12l-2.1 3.5H7.35L5.25 12 6.93 4.5zM8.35 13h6.3l1.4 2.5H6.95l1.4-2.5z" />
                  </svg>
                  Google Drive
                </button>
              )}
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

            {/* Google Drive picker */}
            {inputMode === 'google_drive' && (
              <div className="border-2 border-dashed rounded-xl p-6 border-af-card-border">
                {!googleDriveStatus?.connected ? (
                  <div className="text-center">
                    <svg className="w-12 h-12 mx-auto mb-4 text-white/40" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M7.71 3.5L1.15 15l3.43 6h13.16l3.42-6L14.57 3.5H7.71zm-.78 1h6.21L17.7 12l-2.1 3.5H7.35L5.25 12 6.93 4.5zM8.35 13h6.3l1.4 2.5H6.95l1.4-2.5z" />
                    </svg>
                    <p className="text-white/60 mb-4">Connect your Google Drive to import documents</p>
                    <button
                      onClick={handleConnectGoogleDrive}
                      className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
                    >
                      Connect Google Drive
                    </button>
                  </div>
                ) : loadingDriveFiles ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-af-purple mx-auto mb-4"></div>
                    <p className="text-white/60">Loading your files...</p>
                  </div>
                ) : (
                  <div>
                    {/* Connection status and disconnect button */}
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-sm text-green-400 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-green-400"></span>
                        Connected to Google Drive
                      </span>
                      <button
                        onClick={handleDisconnectGoogleDrive}
                        className="text-sm text-white/40 hover:text-red-400 transition-colors"
                      >
                        Disconnect
                      </button>
                    </div>

                    {/* File list */}
                    {googleDriveFiles.length === 0 ? (
                      <p className="text-center text-white/40 py-4">No compatible documents found in your Drive</p>
                    ) : (
                      <div className="space-y-2 max-h-[200px] overflow-y-auto">
                        {googleDriveFiles.map((driveFile) => (
                          <button
                            key={driveFile.id}
                            onClick={() => setSelectedDriveFile(driveFile)}
                            className={`w-full p-3 rounded-lg text-left transition-colors flex items-center gap-3 ${
                              selectedDriveFile?.id === driveFile.id
                                ? 'bg-af-purple/20 border border-af-purple'
                                : 'bg-af-card hover:bg-white/10 border border-transparent'
                            }`}
                          >
                            <svg className="w-5 h-5 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <div className="flex-1 min-w-0">
                              <p className="text-white text-sm font-medium truncate">{driveFile.name}</p>
                              {driveFile.modifiedTime && (
                                <p className="text-white/40 text-xs">
                                  Modified {new Date(driveFile.modifiedTime).toLocaleDateString()}
                                </p>
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Import button */}
                    {selectedDriveFile && !importedManuscriptPath && (
                      <button
                        onClick={handleImportDriveFile}
                        disabled={driveImporting}
                        className="w-full mt-4 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
                      >
                        {driveImporting ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            Importing...
                          </>
                        ) : (
                          <>Import &quot;{selectedDriveFile.name}&quot;</>
                        )}
                      </button>
                    )}

                    {/* Imported file confirmation */}
                    {importedManuscriptPath && (
                      <div className="mt-4 p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        File imported successfully! Ready to convert.
                      </div>
                    )}
                  </div>
                )}
              </div>
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

            {/* Cover Art Generation */}
            <div className="mt-6 p-4 rounded-lg bg-af-card border border-af-card-border">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <label className="text-sm font-medium text-white/80">
                    Generate AI Cover Art
                  </label>
                  <p className="text-xs text-white/40 mt-1">
                    Create a unique cover image for your audiobook
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setGenerateCover(!generateCover)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    generateCover ? 'bg-af-purple' : 'bg-white/20'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      generateCover ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {generateCover && (
                <div className="mt-4">
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Cover Style
                  </label>
                  <select
                    value={coverVibe}
                    onChange={(e) => setCoverVibe(e.target.value)}
                    className="input-field"
                  >
                    {COVER_VIBES.map((vibe) => (
                      <option key={vibe.id} value={vibe.id}>
                        {vibe.name} - {vibe.description}
                      </option>
                    ))}
                  </select>
                </div>
              )}
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

'use client'

import { useState, useEffect, useCallback } from 'react'
import { GlassCard, PrimaryButton, SecondaryButton } from '@/components/ui'
import {
  getJobTracks,
  getTrackDownloadUrl,
  getJobDownloadUrl,
  type Track,
  type Job,
} from '@/lib/apiClient'

interface TracksViewProps {
  job: Job
}

// Helper to format duration
const formatDuration = (seconds: number | undefined): string => {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Helper to format file size
const formatFileSize = (bytes: number | undefined): string => {
  if (!bytes) return '--'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// Helper to get segment type color
const getSegmentColor = (type: string): string => {
  switch (type) {
    case 'opening_credits':
      return 'bg-green-500/20 text-green-400 border-green-500/30'
    case 'front_matter':
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
    case 'body_chapter':
      return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
    case 'back_matter':
      return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
    case 'closing_credits':
      return 'bg-teal-500/20 text-teal-400 border-teal-500/30'
    case 'retail_sample':
      return 'bg-pink-500/20 text-pink-400 border-pink-500/30'
    default:
      return 'bg-white/10 text-white/60 border-white/10'
  }
}

// Helper to get segment type label
const getSegmentLabel = (type: string): string => {
  switch (type) {
    case 'opening_credits':
      return 'Opening'
    case 'front_matter':
      return 'Front Matter'
    case 'body_chapter':
      return 'Chapter'
    case 'back_matter':
      return 'Back Matter'
    case 'closing_credits':
      return 'Closing'
    case 'retail_sample':
      return 'Sample'
    default:
      return type
  }
}

// Helper to get status color
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'completed':
      return 'text-green-400'
    case 'processing':
      return 'text-yellow-400'
    case 'failed':
      return 'text-red-400'
    default:
      return 'text-white/40'
  }
}

export default function TracksView({ job }: TracksViewProps) {
  const [tracks, setTracks] = useState<Track[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [downloadingTrack, setDownloadingTrack] = useState<string | null>(null)
  const [downloadingAll, setDownloadingAll] = useState(false)
  const [playingTrack, setPlayingTrack] = useState<string | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)

  // Fetch tracks
  const fetchTracks = useCallback(async () => {
    try {
      const data = await getJobTracks(job.id)
      setTracks(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tracks')
    } finally {
      setLoading(false)
    }
  }, [job.id])

  useEffect(() => {
    fetchTracks()
  }, [fetchTracks])

  // Download individual track
  const handleDownloadTrack = async (track: Track) => {
    setDownloadingTrack(track.id)
    try {
      const { download_url, export_filename } = await getTrackDownloadUrl(job.id, track.id)

      // Create download link
      const link = document.createElement('a')
      link.href = download_url
      link.download = export_filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download track')
    } finally {
      setDownloadingTrack(null)
    }
  }

  // Download all (ZIP)
  const handleDownloadAll = async () => {
    setDownloadingAll(true)
    try {
      const { url } = await getJobDownloadUrl(job.id)

      // Create download link
      const link = document.createElement('a')
      link.href = url
      link.download = `${job.title || 'audiobook'}_complete.zip`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download')
    } finally {
      setDownloadingAll(false)
    }
  }

  // Play preview
  const handlePlayPreview = async (track: Track) => {
    if (playingTrack === track.id) {
      // Stop playing
      setPlayingTrack(null)
      setAudioUrl(null)
      return
    }

    try {
      const { download_url } = await getTrackDownloadUrl(job.id, track.id)
      setAudioUrl(download_url)
      setPlayingTrack(track.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audio')
    }
  }

  // Calculate totals
  const completedTracks = tracks.filter(t => t.status === 'completed')
  const totalDuration = completedTracks.reduce((sum, t) => sum + (t.duration_seconds || 0), 0)
  const totalSize = completedTracks.reduce((sum, t) => sum + (t.file_size_bytes || 0), 0)

  if (loading) {
    return (
      <GlassCard className="animate-pulse">
        <div className="h-6 bg-white/10 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-12 bg-white/5 rounded" />
          ))}
        </div>
      </GlassCard>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <GlassCard>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-white mb-1">
              Audio Tracks
            </h2>
            <p className="text-white/60 text-sm">
              {completedTracks.length} tracks &middot; {formatDuration(totalDuration)} total &middot; {formatFileSize(totalSize)}
            </p>
          </div>
          <div className="flex gap-3">
            <SecondaryButton
              onClick={handleDownloadAll}
              disabled={downloadingAll || completedTracks.length === 0}
            >
              {downloadingAll ? 'Preparing...' : 'Download All (ZIP)'}
            </SecondaryButton>
          </div>
        </div>
      </GlassCard>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400">
          {error}
          <button
            onClick={() => setError('')}
            className="ml-2 text-red-400/60 hover:text-red-400"
          >
            &times;
          </button>
        </div>
      )}

      {/* Audio Player (when playing) */}
      {playingTrack && audioUrl && (
        <GlassCard className="bg-af-purple/10 border-af-purple/30">
          <div className="flex items-center gap-4">
            <button
              onClick={() => {
                setPlayingTrack(null)
                setAudioUrl(null)
              }}
              className="p-2 text-white/60 hover:text-white"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div className="flex-1">
              <p className="text-white text-sm mb-2">
                Now Playing: {tracks.find(t => t.id === playingTrack)?.title}
              </p>
              <audio
                controls
                autoPlay
                className="w-full h-10"
                src={audioUrl}
                onEnded={() => {
                  setPlayingTrack(null)
                  setAudioUrl(null)
                }}
              >
                Your browser does not support the audio element.
              </audio>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Track List */}
      <GlassCard>
        {tracks.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-white/60">No tracks available yet.</p>
            <p className="text-white/40 text-sm mt-2">
              Tracks will appear here once audio generation is complete.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {tracks.map((track, index) => (
              <div
                key={track.id}
                className={`
                  py-3 flex items-center gap-4
                  ${index === 0 ? '' : ''}
                  ${track.status !== 'completed' ? 'opacity-50' : ''}
                `}
              >
                {/* Track number */}
                <div className="w-8 text-center text-white/40 text-sm font-mono">
                  {(track.track_index + 1).toString().padStart(2, '0')}
                </div>

                {/* Play button */}
                <button
                  onClick={() => handlePlayPreview(track)}
                  disabled={track.status !== 'completed'}
                  className={`
                    p-2 rounded-full transition-colors
                    ${track.status === 'completed'
                      ? 'text-white/60 hover:text-white hover:bg-white/10'
                      : 'text-white/20 cursor-not-allowed'
                    }
                    ${playingTrack === track.id ? 'text-af-purple bg-af-purple/20' : ''}
                  `}
                >
                  {playingTrack === track.id ? (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  )}
                </button>

                {/* Track info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-white truncate">{track.title}</span>
                    <span className={`px-2 py-0.5 text-xs rounded border ${getSegmentColor(track.segment_type)}`}>
                      {getSegmentLabel(track.segment_type)}
                    </span>
                  </div>
                  <div className="text-sm text-white/40 flex items-center gap-3">
                    <span>{formatDuration(track.duration_seconds)}</span>
                    <span>{formatFileSize(track.file_size_bytes)}</span>
                    {track.export_filename && (
                      <span className="font-mono text-xs">{track.export_filename}</span>
                    )}
                  </div>
                </div>

                {/* Status / Download */}
                <div className="flex items-center gap-2">
                  {track.status !== 'completed' && (
                    <span className={`text-sm ${getStatusColor(track.status)}`}>
                      {track.status === 'processing' ? 'Processing...' : track.status}
                    </span>
                  )}

                  <button
                    onClick={() => handleDownloadTrack(track)}
                    disabled={track.status !== 'completed' || downloadingTrack === track.id}
                    className={`
                      p-2 rounded transition-colors
                      ${track.status === 'completed'
                        ? 'text-white/60 hover:text-white hover:bg-white/10'
                        : 'text-white/20 cursor-not-allowed'
                      }
                    `}
                    title="Download track"
                  >
                    {downloadingTrack === track.id ? (
                      <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Findaway Info */}
      {completedTracks.length > 0 && (
        <GlassCard className="bg-green-500/5 border-green-500/20">
          <div className="flex items-start gap-3">
            <div className="text-green-400 mt-0.5">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="text-green-400 font-medium mb-1">Findaway Ready</h3>
              <p className="text-white/60 text-sm">
                Your audio files are named and formatted for direct upload to Findaway Voices.
                The ZIP download includes all tracks in the correct order with Findaway-compatible filenames.
              </p>
            </div>
          </div>
        </GlassCard>
      )}
    </div>
  )
}

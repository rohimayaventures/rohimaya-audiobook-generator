'use client'

import { useState, useEffect, useCallback } from 'react'
import { GlassCard, PrimaryButton, SecondaryButton } from '@/components/ui'
import {
  getJobChapters,
  updateChapter,
  reorderChapters,
  approveChapters,
  type Chapter,
  type Job,
} from '@/lib/apiClient'

interface ChapterReviewProps {
  job: Job
  onApproved: (updatedJob: Job) => void
}

// Helper to format duration
const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds}s`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`
}

// Helper to get segment type label
const getSegmentLabel = (type: string): string => {
  switch (type) {
    case 'front_matter':
      return 'Front Matter'
    case 'body_chapter':
      return 'Chapter'
    case 'back_matter':
      return 'Back Matter'
    default:
      return type
  }
}

// Helper to get segment type color
const getSegmentColor = (type: string): string => {
  switch (type) {
    case 'front_matter':
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
    case 'body_chapter':
      return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
    case 'back_matter':
      return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
    default:
      return 'bg-white/10 text-white/60 border-white/10'
  }
}

// Helper to get status color
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'approved':
      return 'bg-green-500/20 text-green-400'
    case 'excluded':
      return 'bg-red-500/20 text-red-400'
    case 'pending_review':
    default:
      return 'bg-yellow-500/20 text-yellow-400'
  }
}

export default function ChapterReview({ job, onApproved }: ChapterReviewProps) {
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [approving, setApproving] = useState(false)
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const [expandedChapter, setExpandedChapter] = useState<string | null>(null)

  // Fetch chapters
  const fetchChapters = useCallback(async () => {
    try {
      const data = await getJobChapters(job.id)
      setChapters(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chapters')
    } finally {
      setLoading(false)
    }
  }, [job.id])

  useEffect(() => {
    fetchChapters()
  }, [fetchChapters])

  // Toggle chapter status (approve/exclude)
  const handleToggleStatus = async (chapter: Chapter) => {
    const newStatus = chapter.status === 'approved' ? 'excluded' : 'approved'
    try {
      const updated = await updateChapter(job.id, chapter.id, { status: newStatus })
      setChapters(chapters.map(c => c.id === chapter.id ? updated : c))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update chapter')
    }
  }

  // Change segment type
  const handleSegmentTypeChange = async (chapter: Chapter, segmentType: 'front_matter' | 'body_chapter' | 'back_matter') => {
    try {
      const updated = await updateChapter(job.id, chapter.id, { segment_type: segmentType })
      setChapters(chapters.map(c => c.id === chapter.id ? updated : c))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update chapter')
    }
  }

  // Drag and drop handlers
  const handleDragStart = (index: number) => {
    setDraggedIndex(index)
  }

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    if (draggedIndex === null || draggedIndex === index) return

    // Reorder locally for visual feedback
    const newChapters = [...chapters]
    const draggedChapter = newChapters[draggedIndex]
    newChapters.splice(draggedIndex, 1)
    newChapters.splice(index, 0, draggedChapter)
    setChapters(newChapters)
    setDraggedIndex(index)
  }

  const handleDragEnd = async () => {
    if (draggedIndex === null) return

    // Save new order to backend
    const newOrder = chapters.map(c => c.source_order)
    try {
      const reordered = await reorderChapters(job.id, newOrder)
      setChapters(reordered)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reorder chapters')
      // Refresh to get correct order
      fetchChapters()
    }
    setDraggedIndex(null)
  }

  // Move chapter up/down
  const handleMoveChapter = async (index: number, direction: 'up' | 'down') => {
    const newIndex = direction === 'up' ? index - 1 : index + 1
    if (newIndex < 0 || newIndex >= chapters.length) return

    const newChapters = [...chapters]
    const temp = newChapters[index]
    newChapters[index] = newChapters[newIndex]
    newChapters[newIndex] = temp

    setChapters(newChapters)

    // Save to backend
    const newOrder = newChapters.map(c => c.source_order)
    try {
      const reordered = await reorderChapters(job.id, newOrder)
      setChapters(reordered)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reorder chapters')
      fetchChapters()
    }
  }

  // Approve all and start TTS
  const handleApproveAll = async () => {
    setApproving(true)
    setError('')
    try {
      const updatedJob = await approveChapters(job.id)
      onApproved(updatedJob)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve chapters')
    } finally {
      setApproving(false)
    }
  }

  // Calculate totals
  const approvedChapters = chapters.filter(c => c.status !== 'excluded')
  const totalWords = approvedChapters.reduce((sum, c) => sum + c.word_count, 0)
  const totalDuration = approvedChapters.reduce((sum, c) => sum + c.estimated_duration_seconds, 0)

  if (loading) {
    return (
      <GlassCard className="animate-pulse">
        <div className="h-6 bg-white/10 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-white/5 rounded" />
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
              Review Chapters
            </h2>
            <p className="text-white/60 text-sm">
              Review, reorder, or exclude chapters before generating audio.
              Drag to reorder or use the arrow buttons.
            </p>
          </div>
          <div className="text-right">
            <div className="text-white/40 text-sm">
              {approvedChapters.length} of {chapters.length} chapters
            </div>
            <div className="text-white/60 text-sm">
              ~{totalWords.toLocaleString()} words &middot; ~{formatDuration(totalDuration)}
            </div>
          </div>
        </div>
      </GlassCard>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400">
          {error}
        </div>
      )}

      {/* Chapter List */}
      <GlassCard>
        <div className="space-y-2">
          {chapters.map((chapter, index) => (
            <div
              key={chapter.id}
              draggable
              onDragStart={() => handleDragStart(index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragEnd={handleDragEnd}
              className={`
                border rounded-lg p-4 transition-all cursor-move
                ${chapter.status === 'excluded'
                  ? 'border-white/5 bg-white/5 opacity-50'
                  : 'border-white/10 bg-af-card hover:border-white/20'
                }
                ${draggedIndex === index ? 'ring-2 ring-af-purple' : ''}
              `}
            >
              <div className="flex items-start gap-4">
                {/* Drag handle and order buttons */}
                <div className="flex flex-col items-center gap-1 text-white/40">
                  <button
                    onClick={() => handleMoveChapter(index, 'up')}
                    disabled={index === 0}
                    className="p-1 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Move up"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                    </svg>
                  </button>
                  <span className="text-xs font-mono">{index + 1}</span>
                  <button
                    onClick={() => handleMoveChapter(index, 'down')}
                    disabled={index === chapters.length - 1}
                    className="p-1 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Move down"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </div>

                {/* Chapter info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium text-white truncate">
                      {chapter.title}
                    </h3>
                    <span className={`px-2 py-0.5 text-xs rounded border ${getSegmentColor(chapter.segment_type)}`}>
                      {getSegmentLabel(chapter.segment_type)}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-white/40">
                    <span>{chapter.word_count.toLocaleString()} words</span>
                    <span>~{formatDuration(chapter.estimated_duration_seconds)}</span>
                    {chapter.source_order !== chapter.chapter_index && (
                      <span className="text-amber-400/60">
                        (originally #{chapter.source_order + 1})
                      </span>
                    )}
                  </div>

                  {/* Expandable preview */}
                  {expandedChapter === chapter.id && chapter.text_content && (
                    <div className="mt-3 p-3 bg-black/20 rounded text-sm text-white/70 max-h-40 overflow-y-auto">
                      {chapter.text_content.slice(0, 500)}
                      {chapter.text_content.length > 500 && '...'}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  {/* Segment type dropdown */}
                  <select
                    value={chapter.segment_type}
                    onChange={(e) => handleSegmentTypeChange(chapter, e.target.value as 'front_matter' | 'body_chapter' | 'back_matter')}
                    className="bg-af-dark border border-white/10 rounded px-2 py-1 text-sm text-white/80"
                  >
                    <option value="front_matter">Front Matter</option>
                    <option value="body_chapter">Chapter</option>
                    <option value="back_matter">Back Matter</option>
                  </select>

                  {/* Preview toggle */}
                  <button
                    onClick={() => setExpandedChapter(expandedChapter === chapter.id ? null : chapter.id)}
                    className="p-2 text-white/40 hover:text-white transition-colors"
                    title="Preview"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>

                  {/* Include/Exclude toggle */}
                  <button
                    onClick={() => handleToggleStatus(chapter)}
                    className={`
                      p-2 rounded transition-colors
                      ${chapter.status === 'excluded'
                        ? 'text-red-400 hover:bg-red-500/10'
                        : 'text-green-400 hover:bg-green-500/10'
                      }
                    `}
                    title={chapter.status === 'excluded' ? 'Include in audiobook' : 'Exclude from audiobook'}
                  >
                    {chapter.status === 'excluded' ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Actions */}
      <GlassCard>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="text-white/60">
            <p className="text-sm">
              Ready to generate? This will create audio for{' '}
              <span className="text-white font-medium">{approvedChapters.length}</span> chapters
              (~{formatDuration(totalDuration)} of audio).
            </p>
          </div>
          <div className="flex gap-4">
            <SecondaryButton href="/library">
              Save for later
            </SecondaryButton>
            <PrimaryButton
              onClick={handleApproveAll}
              disabled={approving || approvedChapters.length === 0}
            >
              {approving ? 'Starting...' : 'Generate Audio'}
            </PrimaryButton>
          </div>
        </div>
      </GlassCard>
    </div>
  )
}

'use client'

/**
 * ChapterReview Component
 *
 * Allows users to review, reorder, and approve chapters before audio generation.
 * Features:
 * - Drag-and-drop reordering with visual feedback
 * - Segment type classification (Front Matter, Chapter, Back Matter)
 * - Include/exclude individual chapters
 * - Word count and estimated duration display
 * - Chapter preview expansion
 *
 * Visual primitives used:
 * - GlassCard: Container cards
 * - PrimaryButton/SecondaryButton: Actions
 * - Status badges with segment type colors
 */

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

// Helper to format duration in a readable way
const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds}s`
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }
  return `${mins}m`
}

// Helper to format duration as HH:MM for longer content
const formatDurationLong = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${mins}m`
  }
  return `${mins} min`
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
    case 'opening_credits':
      return 'Opening'
    case 'closing_credits':
      return 'Closing'
    case 'retail_sample':
      return 'Sample'
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
    case 'opening_credits':
      return 'bg-green-500/20 text-green-400 border-green-500/30'
    case 'closing_credits':
      return 'bg-teal-500/20 text-teal-400 border-teal-500/30'
    case 'retail_sample':
      return 'bg-pink-500/20 text-pink-400 border-pink-500/30'
    default:
      return 'bg-white/10 text-white/60 border-white/10'
  }
}

export default function ChapterReview({ job, onApproved }: ChapterReviewProps) {
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [approving, setApproving] = useState(false)
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const [expandedChapter, setExpandedChapter] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

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

  // Toggle chapter status (include/exclude)
  const handleToggleStatus = async (chapter: Chapter) => {
    const newStatus = chapter.status === 'excluded' ? 'pending_review' : 'excluded'
    setSaving(true)
    try {
      const updated = await updateChapter(job.id, chapter.id, { status: newStatus })
      setChapters(chapters.map(c => c.id === chapter.id ? updated : c))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update chapter')
    } finally {
      setSaving(false)
    }
  }

  // Change segment type
  const handleSegmentTypeChange = async (chapter: Chapter, segmentType: 'front_matter' | 'body_chapter' | 'back_matter') => {
    setSaving(true)
    try {
      const updated = await updateChapter(job.id, chapter.id, { segment_type: segmentType })
      setChapters(chapters.map(c => c.id === chapter.id ? updated : c))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update chapter')
    } finally {
      setSaving(false)
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
    setSaving(true)
    try {
      const reordered = await reorderChapters(job.id, newOrder)
      setChapters(reordered)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reorder chapters')
      // Refresh to get correct order
      fetchChapters()
    } finally {
      setSaving(false)
    }
    setDraggedIndex(null)
  }

  // Move chapter up/down with arrow buttons
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
    setSaving(true)
    try {
      const reordered = await reorderChapters(job.id, newOrder)
      setChapters(reordered)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reorder chapters')
      fetchChapters()
    } finally {
      setSaving(false)
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
  const includedChapters = chapters.filter(c => c.status !== 'excluded')
  const bodyChapters = includedChapters.filter(c => c.segment_type === 'body_chapter')
  const totalWords = includedChapters.reduce((sum, c) => sum + c.word_count, 0)
  const totalDuration = includedChapters.reduce((sum, c) => sum + c.estimated_duration_seconds, 0)

  // Validation: Must have at least one body chapter
  const canApprove = bodyChapters.length > 0

  if (loading) {
    return (
      <GlassCard className="animate-pulse">
        <div className="h-6 bg-white/10 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-20 bg-white/5 rounded" />
          ))}
        </div>
      </GlassCard>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <GlassCard glow>
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
          <div>
            <h2 className="text-xl font-semibold text-white mb-2">
              Review & Arrange Chapters
            </h2>
            <p className="text-white/60 text-sm max-w-xl">
              Confirm the order, type, and inclusion of each section before we generate your audiobook.
              Drag to reorder or use the arrow buttons. You can exclude chapters you don&apos;t want narrated.
            </p>
          </div>

          {/* Summary Stats */}
          <div className="flex gap-6 text-right">
            <div>
              <div className="text-2xl font-bold text-white">{includedChapters.length}</div>
              <div className="text-xs text-white/40">Chapters</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{totalWords.toLocaleString()}</div>
              <div className="text-xs text-white/40">Words</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{formatDurationLong(totalDuration)}</div>
              <div className="text-xs text-white/40">Est. Duration</div>
            </div>
          </div>
        </div>

        {/* Saving indicator */}
        {saving && (
          <div className="flex items-center gap-2 text-white/40 text-sm">
            <span className="w-2 h-2 bg-af-purple rounded-full animate-pulse" />
            Saving changes...
          </div>
        )}
      </GlassCard>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400 flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={() => setError('')}
            className="text-red-400/60 hover:text-red-400"
          >
            ✕
          </button>
        </div>
      )}

      {/* Chapter List */}
      <GlassCard>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-white">Chapter Order</h3>
          <div className="text-sm text-white/40">
            {chapters.filter(c => c.status === 'excluded').length > 0 && (
              <span className="text-amber-400">
                {chapters.filter(c => c.status === 'excluded').length} excluded
              </span>
            )}
          </div>
        </div>

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
                ${draggedIndex === index ? 'ring-2 ring-af-purple shadow-glow' : ''}
              `}
            >
              <div className="flex items-start gap-4">
                {/* Drag handle and order buttons */}
                <div className="flex flex-col items-center gap-1 text-white/40 select-none">
                  <button
                    onClick={() => handleMoveChapter(index, 'up')}
                    disabled={index === 0}
                    className="p-1 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    title="Move up"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                    </svg>
                  </button>
                  <div className="w-6 h-6 rounded bg-white/5 flex items-center justify-center">
                    <span className="text-xs font-mono text-white/60">{index + 1}</span>
                  </div>
                  <button
                    onClick={() => handleMoveChapter(index, 'down')}
                    disabled={index === chapters.length - 1}
                    className="p-1 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    title="Move down"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </div>

                {/* Chapter info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <h4 className="font-medium text-white truncate">
                      {chapter.display_title || chapter.title}
                    </h4>
                    <span className={`px-2 py-0.5 text-xs rounded border flex-shrink-0 ${getSegmentColor(chapter.segment_type)}`}>
                      {getSegmentLabel(chapter.segment_type)}
                    </span>
                    {chapter.status === 'excluded' && (
                      <span className="px-2 py-0.5 text-xs rounded bg-red-500/20 text-red-400 border border-red-500/30">
                        Excluded
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-white/40">
                    <span>{chapter.word_count.toLocaleString()} words</span>
                    <span>~{formatDuration(chapter.estimated_duration_seconds)}</span>
                    {chapter.source_order !== chapter.chapter_index && (
                      <span className="text-amber-400/60 text-xs">
                        (was #{chapter.source_order + 1})
                      </span>
                    )}
                  </div>

                  {/* Expandable preview */}
                  {expandedChapter === chapter.id && chapter.text_content && (
                    <div className="mt-3 p-3 bg-black/30 rounded-lg text-sm text-white/70 max-h-48 overflow-y-auto border border-white/5">
                      <p className="whitespace-pre-wrap leading-relaxed">
                        {chapter.text_content.slice(0, 800)}
                        {chapter.text_content.length > 800 && '...'}
                      </p>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  {/* Segment type dropdown */}
                  <select
                    value={chapter.segment_type}
                    onChange={(e) => handleSegmentTypeChange(chapter, e.target.value as 'front_matter' | 'body_chapter' | 'back_matter')}
                    className="bg-af-dark border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white/80 cursor-pointer hover:border-white/20 transition-colors"
                  >
                    <option value="front_matter">Front Matter</option>
                    <option value="body_chapter">Chapter</option>
                    <option value="back_matter">Back Matter</option>
                  </select>

                  {/* Preview toggle */}
                  <button
                    onClick={() => setExpandedChapter(expandedChapter === chapter.id ? null : chapter.id)}
                    className={`
                      p-2 rounded-lg transition-colors
                      ${expandedChapter === chapter.id
                        ? 'text-af-purple bg-af-purple/10'
                        : 'text-white/40 hover:text-white hover:bg-white/5'
                      }
                    `}
                    title={expandedChapter === chapter.id ? 'Hide preview' : 'Show preview'}
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
                      p-2 rounded-lg transition-colors
                      ${chapter.status === 'excluded'
                        ? 'text-red-400 bg-red-500/10 hover:bg-red-500/20'
                        : 'text-green-400 bg-green-500/10 hover:bg-green-500/20'
                      }
                    `}
                    title={chapter.status === 'excluded' ? 'Include in audiobook' : 'Exclude from audiobook'}
                  >
                    {chapter.status === 'excluded' ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
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

        {chapters.length === 0 && (
          <div className="text-center py-8 text-white/40">
            <p>No chapters detected in your manuscript.</p>
            <p className="text-sm mt-2">Try uploading a different file or contact support.</p>
          </div>
        )}
      </GlassCard>

      {/* Action Footer */}
      <GlassCard>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="text-white/60">
            {canApprove ? (
              <p className="text-sm">
                Ready to generate? This will create audio for{' '}
                <span className="text-white font-medium">{includedChapters.length}</span> sections
                ({formatDurationLong(totalDuration)} estimated).
              </p>
            ) : (
              <p className="text-sm text-amber-400">
                You need at least one body chapter to generate an audiobook.
                Check your chapter types above.
              </p>
            )}
          </div>
          <div className="flex gap-4">
            <SecondaryButton href="/library">
              Save for later
            </SecondaryButton>
            <PrimaryButton
              onClick={handleApproveAll}
              disabled={approving || !canApprove}
              loading={approving}
            >
              {approving ? 'Starting...' : 'Approve & Generate Audio'}
            </PrimaryButton>
          </div>
        </div>
      </GlassCard>
    </div>
  )
}

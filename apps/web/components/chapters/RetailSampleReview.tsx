'use client'

import { useState, useEffect, useCallback } from 'react'
import { GlassCard, PrimaryButton, SecondaryButton } from '@/components/ui'
import {
  getRetailSamples,
  confirmRetailSample,
  updateRetailSample,
  regenerateRetailSamples,
  type RetailSample,
  type Job,
} from '@/lib/apiClient'

interface RetailSampleReviewProps {
  job: Job
  onConfirmed?: (sample: RetailSample) => void
  onSkip?: () => void
}

// Helper to format duration
const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds}s`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`
}

// Helper to format score as percentage
const formatScore = (score?: number): string => {
  if (score === undefined || score === null) return '--'
  return `${Math.round(score * 100)}%`
}

// Helper to get score color
const getScoreColor = (score?: number): string => {
  if (score === undefined || score === null) return 'text-white/40'
  if (score >= 0.7) return 'text-green-400'
  if (score >= 0.4) return 'text-yellow-400'
  return 'text-red-400'
}

// For spoiler risk, lower is better (inverted)
const getSpoilerColor = (score?: number): string => {
  if (score === undefined || score === null) return 'text-white/40'
  if (score <= 0.3) return 'text-green-400'
  if (score <= 0.6) return 'text-yellow-400'
  return 'text-red-400'
}

export default function RetailSampleReview({ job, onConfirmed, onSkip }: RetailSampleReviewProps) {
  const [samples, setSamples] = useState<RetailSample[]>([])
  const [selectedSample, setSelectedSample] = useState<RetailSample | null>(null)
  const [editedText, setEditedText] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  // Fetch retail samples
  const fetchSamples = useCallback(async () => {
    try {
      setLoading(true)
      const data = await getRetailSamples(job.id)
      setSamples(data)

      // Select the best candidate by default (highest overall score)
      if (data.length > 0) {
        const best = data.reduce((prev, curr) =>
          (curr.overall_score || 0) > (prev.overall_score || 0) ? curr : prev
        )
        setSelectedSample(best)
        setEditedText(best.user_edited_text || best.sample_text)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load retail samples')
    } finally {
      setLoading(false)
    }
  }, [job.id])

  useEffect(() => {
    fetchSamples()
  }, [fetchSamples])

  // Handle sample selection
  const handleSelectSample = (sample: RetailSample) => {
    setSelectedSample(sample)
    setEditedText(sample.user_edited_text || sample.sample_text)
    setIsEditing(false)
  }

  // Handle text editing
  const handleSaveEdit = async () => {
    if (!selectedSample) return

    setSaving(true)
    setError('')
    try {
      const updated = await updateRetailSample(job.id, selectedSample.id, {
        user_edited_text: editedText
      })
      setSamples(samples.map(s => s.id === updated.id ? updated : s))
      setSelectedSample(updated)
      setIsEditing(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save changes')
    } finally {
      setSaving(false)
    }
  }

  // Handle regeneration
  const handleRegenerate = async () => {
    setRegenerating(true)
    setError('')
    try {
      const newSamples = await regenerateRetailSamples(job.id)
      setSamples(newSamples)
      if (newSamples.length > 0) {
        const best = newSamples.reduce((prev, curr) =>
          (curr.overall_score || 0) > (prev.overall_score || 0) ? curr : prev
        )
        setSelectedSample(best)
        setEditedText(best.sample_text)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate samples')
    } finally {
      setRegenerating(false)
    }
  }

  // Handle confirmation
  const handleConfirm = async () => {
    if (!selectedSample) return

    setConfirming(true)
    setError('')
    try {
      const confirmed = await confirmRetailSample(job.id, selectedSample.id)
      onConfirmed?.(confirmed)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to confirm sample')
    } finally {
      setConfirming(false)
    }
  }

  // Calculate word count for edited text
  const wordCount = editedText.trim().split(/\s+/).filter(w => w.length > 0).length
  const estimatedDuration = Math.round((wordCount / 150) * 60)

  if (loading) {
    return (
      <GlassCard className="animate-pulse">
        <div className="h-6 bg-white/10 rounded w-1/3 mb-4" />
        <div className="h-40 bg-white/5 rounded" />
      </GlassCard>
    )
  }

  if (samples.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-8">
          <div className="text-4xl mb-4">📄</div>
          <h3 className="text-lg font-semibold text-white mb-2">No Retail Sample Candidates</h3>
          <p className="text-white/60 mb-6">
            The system couldn&apos;t find suitable excerpts for a retail sample.
            You can skip this step or try regenerating.
          </p>
          <div className="flex justify-center gap-4">
            <SecondaryButton onClick={handleRegenerate} disabled={regenerating}>
              {regenerating ? 'Regenerating...' : 'Try Again'}
            </SecondaryButton>
            <PrimaryButton onClick={onSkip}>
              Skip Retail Sample
            </PrimaryButton>
          </div>
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
              Retail Sample Selection
            </h2>
            <p className="text-white/60 text-sm">
              Choose or edit the excerpt that will be used as your audiobook&apos;s retail sample.
              This is what potential buyers will hear.
            </p>
          </div>
          <div className="flex gap-2">
            <SecondaryButton
              onClick={handleRegenerate}
              disabled={regenerating}
              size="sm"
            >
              {regenerating ? 'Regenerating...' : 'Regenerate'}
            </SecondaryButton>
          </div>
        </div>
      </GlassCard>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sample Candidates */}
        <div className="lg:col-span-1">
          <GlassCard>
            <h3 className="text-lg font-medium text-white mb-4">Candidates</h3>
            <div className="space-y-3">
              {samples.map((sample, index) => (
                <button
                  key={sample.id}
                  onClick={() => handleSelectSample(sample)}
                  className={`
                    w-full p-3 rounded-lg text-left transition-all
                    ${selectedSample?.id === sample.id
                      ? 'bg-af-purple/20 border-2 border-af-purple'
                      : 'bg-af-card border border-white/10 hover:border-white/20'
                    }
                  `}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white">
                      Option {index + 1}
                    </span>
                    {sample.overall_score !== undefined && (
                      <span className={`text-sm font-mono ${getScoreColor(sample.overall_score)}`}>
                        {formatScore(sample.overall_score)}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-white/40 mb-2">
                    {sample.source_chapter_title && (
                      <span>From: {sample.source_chapter_title}</span>
                    )}
                  </div>
                  <div className="text-xs text-white/50 line-clamp-2">
                    {sample.sample_text.slice(0, 100)}...
                  </div>
                  <div className="flex items-center gap-3 mt-2 text-xs text-white/40">
                    <span>{sample.word_count} words</span>
                    <span>~{formatDuration(sample.estimated_duration_seconds)}</span>
                  </div>
                </button>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* Selected Sample Preview/Edit */}
        <div className="lg:col-span-2">
          <GlassCard>
            {selectedSample ? (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-white">
                    {isEditing ? 'Edit Sample' : 'Preview'}
                  </h3>
                  <div className="flex gap-2">
                    {isEditing ? (
                      <>
                        <SecondaryButton
                          onClick={() => {
                            setIsEditing(false)
                            setEditedText(selectedSample.user_edited_text || selectedSample.sample_text)
                          }}
                          size="sm"
                        >
                          Cancel
                        </SecondaryButton>
                        <PrimaryButton
                          onClick={handleSaveEdit}
                          disabled={saving}
                          size="sm"
                        >
                          {saving ? 'Saving...' : 'Save'}
                        </PrimaryButton>
                      </>
                    ) : (
                      <SecondaryButton
                        onClick={() => setIsEditing(true)}
                        size="sm"
                      >
                        Edit Text
                      </SecondaryButton>
                    )}
                  </div>
                </div>

                {/* AI Scores */}
                {selectedSample.overall_score !== undefined && (
                  <div className="grid grid-cols-4 gap-4 mb-4 p-3 bg-af-dark rounded-lg">
                    <div className="text-center">
                      <div className="text-xs text-white/40 mb-1">Engagement</div>
                      <div className={`font-mono ${getScoreColor(selectedSample.engagement_score)}`}>
                        {formatScore(selectedSample.engagement_score)}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-white/40 mb-1">Intensity</div>
                      <div className={`font-mono ${getScoreColor(selectedSample.emotional_intensity_score)}`}>
                        {formatScore(selectedSample.emotional_intensity_score)}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-white/40 mb-1">Spoiler Risk</div>
                      <div className={`font-mono ${getSpoilerColor(selectedSample.spoiler_risk_score)}`}>
                        {formatScore(selectedSample.spoiler_risk_score)}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-white/40 mb-1">Overall</div>
                      <div className={`font-mono font-bold ${getScoreColor(selectedSample.overall_score)}`}>
                        {formatScore(selectedSample.overall_score)}
                      </div>
                    </div>
                  </div>
                )}

                {/* Text content */}
                {isEditing ? (
                  <textarea
                    value={editedText}
                    onChange={(e) => setEditedText(e.target.value)}
                    className="w-full h-64 p-4 bg-af-dark border border-white/10 rounded-lg text-white/90 text-sm leading-relaxed resize-none focus:outline-none focus:border-af-purple"
                    placeholder="Edit your retail sample text..."
                  />
                ) : (
                  <div className="h-64 p-4 bg-af-dark rounded-lg overflow-y-auto">
                    <p className="text-white/90 text-sm leading-relaxed whitespace-pre-wrap">
                      {selectedSample.user_edited_text || selectedSample.sample_text}
                    </p>
                  </div>
                )}

                {/* Stats */}
                <div className="flex items-center justify-between mt-4 text-sm text-white/40">
                  <div className="flex gap-4">
                    <span>{wordCount} words</span>
                    <span>~{formatDuration(estimatedDuration)}</span>
                  </div>
                  {wordCount < 400 && (
                    <span className="text-amber-400">
                      Recommended: 400-900 words
                    </span>
                  )}
                  {wordCount > 900 && (
                    <span className="text-amber-400">
                      Consider trimming to 400-900 words
                    </span>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-white/40">
                Select a sample candidate to preview
              </div>
            )}
          </GlassCard>
        </div>
      </div>

      {/* Actions */}
      <GlassCard>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="text-white/60">
            <p className="text-sm">
              The retail sample is a {formatDuration(estimatedDuration)} preview that potential listeners
              will hear before purchasing your audiobook.
            </p>
          </div>
          <div className="flex gap-4">
            <SecondaryButton onClick={onSkip}>
              Skip for now
            </SecondaryButton>
            <PrimaryButton
              onClick={handleConfirm}
              disabled={confirming || !selectedSample}
            >
              {confirming ? 'Confirming...' : 'Confirm Selection'}
            </PrimaryButton>
          </div>
        </div>
      </GlassCard>
    </div>
  )
}

export { RetailSampleReview }

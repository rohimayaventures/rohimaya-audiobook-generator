'use client'

import { clsx } from 'clsx'
import { PrimaryButton } from './PrimaryButton'
import { SecondaryButton } from './SecondaryButton'

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description: string
  primaryAction?: {
    label: string
    href?: string
    onClick?: () => void
  }
  secondaryAction?: {
    label: string
    href?: string
    onClick?: () => void
  }
  className?: string
}

/**
 * EmptyState - Illustrated placeholder for empty lists
 */
export function EmptyState({
  icon,
  title,
  description,
  primaryAction,
  secondaryAction,
  className,
}: EmptyStateProps) {
  return (
    <div className={clsx(
      'flex flex-col items-center justify-center py-16 px-6 text-center',
      className
    )}>
      {/* Icon or Default Illustration */}
      {icon || (
        <div className="w-24 h-24 mb-6 relative">
          <svg
            viewBox="0 0 96 96"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="w-full h-full"
          >
            {/* Microphone illustration */}
            <circle cx="48" cy="48" r="46" className="fill-white/5 stroke-white/10" strokeWidth="2" />
            <rect x="38" y="24" width="20" height="32" rx="10" className="fill-af-purple/30 stroke-af-purple" strokeWidth="2" />
            <path d="M32 44v8a16 16 0 0032 0v-8" className="stroke-af-purple-soft" strokeWidth="2" strokeLinecap="round" />
            <line x1="48" y1="68" x2="48" y2="76" className="stroke-af-purple-soft" strokeWidth="2" strokeLinecap="round" />
            <line x1="40" y1="76" x2="56" y2="76" className="stroke-af-purple-soft" strokeWidth="2" strokeLinecap="round" />
          </svg>
          {/* Decorative sparkles */}
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-af-purple rounded-full animate-pulse" />
          <div className="absolute top-4 -left-2 w-2 h-2 bg-af-purple-soft rounded-full animate-pulse delay-75" />
        </div>
      )}

      {/* Title */}
      <h3 className="text-xl font-semibold text-white mb-2">
        {title}
      </h3>

      {/* Description */}
      <p className="text-af-text-muted max-w-md mb-6">
        {description}
      </p>

      {/* Actions */}
      {(primaryAction || secondaryAction) && (
        <div className="flex flex-col sm:flex-row gap-3">
          {primaryAction && (
            <PrimaryButton
              href={primaryAction.href}
              onClick={primaryAction.onClick}
            >
              {primaryAction.label}
            </PrimaryButton>
          )}
          {secondaryAction && (
            <SecondaryButton
              href={secondaryAction.href}
              onClick={secondaryAction.onClick}
            >
              {secondaryAction.label}
            </SecondaryButton>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Pre-configured empty states for common scenarios
 */
export function NoAudiobooksState() {
  return (
    <EmptyState
      icon={
        <div className="w-24 h-24 mb-6 relative">
          <svg viewBox="0 0 96 96" fill="none" className="w-full h-full">
            <circle cx="48" cy="48" r="46" className="fill-white/5 stroke-white/10" strokeWidth="2" />
            <rect x="28" y="20" width="40" height="52" rx="4" className="fill-af-purple/20 stroke-af-purple" strokeWidth="2" />
            <line x1="36" y1="32" x2="60" y2="32" className="stroke-af-purple-soft" strokeWidth="2" strokeLinecap="round" />
            <line x1="36" y1="42" x2="56" y2="42" className="stroke-af-purple-soft/60" strokeWidth="2" strokeLinecap="round" />
            <line x1="36" y1="52" x2="52" y2="52" className="stroke-af-purple-soft/40" strokeWidth="2" strokeLinecap="round" />
            {/* Sound waves */}
            <path d="M68 38c4 4 4 16 0 20" className="stroke-af-purple" strokeWidth="2" strokeLinecap="round" />
            <path d="M74 32c8 8 8 24 0 32" className="stroke-af-purple/60" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-af-purple rounded-full animate-pulse" />
        </div>
      }
      title="No audiobooks yet"
      description="Transform your first manuscript into a professional audiobook. Upload a document or paste your text to get started."
      primaryAction={{
        label: "Create Your First Audiobook",
        href: "/dashboard",
      }}
    />
  )
}

export function NoFailedJobsState() {
  return (
    <EmptyState
      icon={
        <div className="w-20 h-20 mb-4 rounded-full bg-green-500/20 flex items-center justify-center">
          <svg className="w-10 h-10 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      }
      title="All clear!"
      description="You don't have any failed audiobook conversions. All your projects are running smoothly."
    />
  )
}

export function NoGoogleDriveState({ onConnect }: { onConnect?: () => void }) {
  return (
    <EmptyState
      icon={
        <div className="w-24 h-24 mb-6">
          <svg viewBox="0 0 96 96" fill="none" className="w-full h-full">
            <circle cx="48" cy="48" r="46" className="fill-white/5 stroke-white/10" strokeWidth="2" />
            {/* Google Drive icon stylized */}
            <path d="M32 36l16 28h16l-16-28H32z" className="fill-yellow-500/30 stroke-yellow-500" strokeWidth="2" />
            <path d="M48 36l16 28h16L64 36H48z" className="fill-blue-500/30 stroke-blue-500" strokeWidth="2" />
            <path d="M32 36h16l8 14H40L32 36z" className="fill-green-500/30 stroke-green-500" strokeWidth="2" />
          </svg>
        </div>
      }
      title="Connect Google Drive"
      description="Import manuscripts directly from your Google Drive. Connect once and access all your documents instantly."
      primaryAction={{
        label: "Connect Google Drive",
        onClick: onConnect,
      }}
    />
  )
}

export function NoTracksState() {
  return (
    <EmptyState
      icon={
        <div className="w-20 h-20 mb-4 rounded-full bg-af-purple/20 flex items-center justify-center">
          <svg className="w-10 h-10 text-af-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
          </svg>
        </div>
      }
      title="No audio tracks yet"
      description="Audio tracks will appear here once your audiobook generation is complete. This usually takes a few minutes."
    />
  )
}

export function NoChaptersState() {
  return (
    <EmptyState
      icon={
        <div className="w-20 h-20 mb-4 rounded-full bg-amber-500/20 flex items-center justify-center">
          <svg className="w-10 h-10 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </div>
      }
      title="No chapters detected"
      description="We couldn't detect chapters in your manuscript. You can still proceed - the entire text will be converted as one continuous narration."
    />
  )
}

export default EmptyState

'use client'

import { clsx } from 'clsx'

interface SkeletonProps {
  className?: string
  variant?: 'text' | 'circular' | 'rectangular' | 'card'
  width?: string | number
  height?: string | number
  lines?: number
}

/**
 * Skeleton - Loading placeholder with pulse animation
 */
export function Skeleton({
  className,
  variant = 'rectangular',
  width,
  height,
  lines = 1,
}: SkeletonProps) {
  const baseClasses = 'animate-pulse bg-white/10 rounded'

  const variantClasses = {
    text: 'h-4 rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
    card: 'rounded-xl',
  }

  const style = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  }

  if (variant === 'text' && lines > 1) {
    return (
      <div className={clsx('space-y-2', className)}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={clsx(baseClasses, variantClasses.text)}
            style={{
              ...style,
              width: i === lines - 1 ? '75%' : style.width, // Last line shorter
            }}
          />
        ))}
      </div>
    )
  }

  return (
    <div
      className={clsx(baseClasses, variantClasses[variant], className)}
      style={style}
    />
  )
}

/**
 * SkeletonCard - Card-shaped loading placeholder
 */
export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={clsx(
      'bg-af-card backdrop-blur-xl border border-af-card-border rounded-xl p-6',
      className
    )}>
      <div className="flex items-start gap-4">
        <Skeleton variant="circular" width={48} height={48} />
        <div className="flex-1 space-y-3">
          <Skeleton variant="text" width="60%" height={20} />
          <Skeleton variant="text" width="40%" height={16} />
        </div>
      </div>
      <div className="mt-4 space-y-2">
        <Skeleton variant="text" lines={3} />
      </div>
      <div className="mt-4 flex gap-2">
        <Skeleton variant="rectangular" width={80} height={32} />
        <Skeleton variant="rectangular" width={80} height={32} />
      </div>
    </div>
  )
}

/**
 * SkeletonJobCard - Job card loading placeholder
 */
export function SkeletonJobCard() {
  return (
    <div className="bg-af-card backdrop-blur-xl border border-af-card-border rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <Skeleton variant="text" width="50%" height={24} />
        <Skeleton variant="rectangular" width={80} height={24} className="rounded-full" />
      </div>
      <div className="space-y-2 mb-4">
        <Skeleton variant="text" width="70%" height={14} />
        <Skeleton variant="text" width="40%" height={14} />
      </div>
      <div className="flex items-center gap-3">
        <Skeleton variant="rectangular" width={100} height={36} />
        <Skeleton variant="rectangular" width={100} height={36} />
      </div>
    </div>
  )
}

/**
 * SkeletonVoiceOption - Voice selector loading placeholder
 */
export function SkeletonVoiceOption() {
  return (
    <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
      <Skeleton variant="circular" width={40} height={40} />
      <div className="flex-1">
        <Skeleton variant="text" width="60%" height={16} />
        <Skeleton variant="text" width="80%" height={12} className="mt-1" />
      </div>
      <Skeleton variant="rectangular" width={60} height={28} />
    </div>
  )
}

/**
 * SkeletonTable - Table loading placeholder
 */
export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex gap-4 p-3 bg-white/5 rounded-lg">
        <Skeleton variant="text" width="25%" height={16} />
        <Skeleton variant="text" width="20%" height={16} />
        <Skeleton variant="text" width="15%" height={16} />
        <Skeleton variant="text" width="20%" height={16} />
        <Skeleton variant="text" width="20%" height={16} />
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 p-3">
          <Skeleton variant="text" width="25%" height={14} />
          <Skeleton variant="text" width="20%" height={14} />
          <Skeleton variant="text" width="15%" height={14} />
          <Skeleton variant="text" width="20%" height={14} />
          <Skeleton variant="rectangular" width={60} height={28} />
        </div>
      ))}
    </div>
  )
}

export default Skeleton

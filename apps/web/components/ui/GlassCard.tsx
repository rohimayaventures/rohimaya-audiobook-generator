import { clsx } from 'clsx'

interface GlassCardProps {
  children: React.ReactNode
  title?: string
  className?: string
  variant?: 'default' | 'feature' | 'compact'
  glow?: boolean
  'data-tour'?: string
}

/**
 * GlassCard - Glassmorphism card component
 * Used throughout the app for content containers
 */
export function GlassCard({
  children,
  title,
  className,
  variant = 'default',
  glow = false,
  'data-tour': dataTour,
}: GlassCardProps) {
  return (
    <div
      data-tour={dataTour}
      className={clsx(
        'glass transition-all duration-300',
        {
          'p-6 md:p-8': variant === 'default',
          'p-5 md:p-6': variant === 'feature',
          'p-4': variant === 'compact',
          'hover:shadow-glow hover:border-af-purple-soft/30': glow,
          'glow-border': glow,
        },
        className
      )}
    >
      {title && (
        <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
      )}
      {children}
    </div>
  )
}

export default GlassCard

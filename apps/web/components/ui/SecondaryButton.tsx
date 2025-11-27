import { clsx } from 'clsx'
import Link from 'next/link'

export interface SecondaryButtonProps {
  children: React.ReactNode
  href?: string
  onClick?: () => void
  type?: 'button' | 'submit'
  disabled?: boolean
  loading?: boolean
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

/**
 * SecondaryButton - Glass-style outlined button for secondary actions
 */
export function SecondaryButton({
  children,
  href,
  onClick,
  type = 'button',
  disabled = false,
  loading = false,
  className,
  size = 'md',
}: SecondaryButtonProps) {
  const sizeClasses = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
  }

  const baseClasses = clsx(
    'inline-flex items-center justify-center gap-2 rounded-xl font-semibold text-white',
    'bg-af-card backdrop-blur-xl border border-af-card-border',
    'hover:bg-white/10 hover:border-af-purple-soft/50',
    'transition-all duration-300 ease-out',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    sizeClasses[size],
    className
  )

  if (href && !disabled) {
    return (
      <Link href={href} className={baseClasses}>
        {children}
      </Link>
    )
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={baseClasses}
    >
      {loading ? (
        <>
          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {children}
        </>
      ) : (
        children
      )}
    </button>
  )
}

export default SecondaryButton

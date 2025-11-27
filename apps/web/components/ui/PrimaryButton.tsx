import { clsx } from 'clsx'
import Link from 'next/link'

interface PrimaryButtonProps {
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
 * PrimaryButton - Glowing gradient button for main CTAs
 */
export function PrimaryButton({
  children,
  href,
  onClick,
  type = 'button',
  disabled = false,
  loading = false,
  className,
  size = 'md',
}: PrimaryButtonProps) {
  const sizeClasses = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
  }

  const baseClasses = clsx(
    'inline-flex items-center justify-center gap-2 rounded-xl font-semibold text-white',
    'bg-gradient-to-r from-af-purple to-af-pink',
    'shadow-glow hover:shadow-glow-lg',
    'transition-all duration-300 ease-out',
    'hover:scale-105 active:scale-95',
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100',
    sizeClasses[size],
    className
  )

  const content = (
    <>
      {loading && (
        <svg
          className="animate-spin h-5 w-5"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </>
  )

  if (href && !disabled) {
    return (
      <Link href={href} className={baseClasses}>
        {content}
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
      {content}
    </button>
  )
}

export default PrimaryButton

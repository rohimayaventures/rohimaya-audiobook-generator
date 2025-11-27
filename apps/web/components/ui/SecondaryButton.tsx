import { clsx } from 'clsx'
import Link from 'next/link'

interface SecondaryButtonProps {
  children: React.ReactNode
  href?: string
  onClick?: () => void
  type?: 'button' | 'submit'
  disabled?: boolean
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
      disabled={disabled}
      className={baseClasses}
    >
      {children}
    </button>
  )
}

export default SecondaryButton

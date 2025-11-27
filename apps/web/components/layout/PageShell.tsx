interface PageShellProps {
  children: React.ReactNode
  title?: string
  subtitle?: string
  className?: string
}

/**
 * PageShell - Consistent wrapper for dashboard pages
 * Provides padding, max-width, and optional title
 */
export function PageShell({ children, title, subtitle, className = '' }: PageShellProps) {
  return (
    <div className={`min-h-screen pt-24 pb-16 px-4 sm:px-6 lg:px-8 ${className}`}>
      <div className="max-w-6xl mx-auto">
        {(title || subtitle) && (
          <div className="mb-8">
            {title && (
              <h1 className="text-3xl font-bold text-white mb-2">{title}</h1>
            )}
            {subtitle && (
              <p className="text-white/60">{subtitle}</p>
            )}
          </div>
        )}
        {children}
      </div>
    </div>
  )
}

export default PageShell

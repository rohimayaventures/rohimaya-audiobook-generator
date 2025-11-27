'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'
import { clsx } from 'clsx'

interface NavbarProps {
  user?: {
    email?: string
    user_metadata?: {
      display_name?: string
    }
  } | null
  onLogout?: () => void
}

/**
 * Navbar - Main navigation component
 * Shows different links based on auth state
 */
export function Navbar({ user, onLogout }: NavbarProps) {
  const pathname = usePathname()
  const [menuOpen, setMenuOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const isActive = (path: string) => pathname === path

  // Get display name or fallback to email username
  const getDisplayName = () => {
    return user?.user_metadata?.display_name || user?.email?.split('@')[0] || 'User'
  }

  // Get first letter for avatar
  const getAvatarLetter = () => {
    const name = user?.user_metadata?.display_name || user?.email
    return name?.[0]?.toUpperCase() || 'U'
  }

  const navLinks = user
    ? [
        { href: '/dashboard', label: 'Dashboard' },
        { href: '/library', label: 'Library' },
        { href: '/pricing', label: 'Pricing' },
      ]
    : [
        { href: '/pricing', label: 'Pricing' },
      ]

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-af-midnight/80 border-b border-af-card-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo - links to dashboard if logged in, homepage if not */}
          <Link href={user ? "/dashboard" : "/"} className="flex items-center gap-2">
            <span className="font-serif text-xl font-bold text-gradient">
              AuthorFlow
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={clsx(
                  'text-sm font-medium transition-colors',
                  isActive(link.href)
                    ? 'text-af-lavender'
                    : 'text-white/70 hover:text-white'
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Auth buttons / User menu */}
          <div className="hidden md:flex items-center gap-4">
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 text-sm text-white/80 hover:text-white transition-colors"
                >
                  {/* Avatar */}
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-af-purple to-af-pink flex items-center justify-center text-white text-xs font-bold">
                    {getAvatarLetter()}
                  </div>
                  <span className="hidden sm:inline text-sm">{getDisplayName()}</span>
                  <svg
                    className={clsx('w-4 h-4 transition-transform', userMenuOpen && 'rotate-180')}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Dropdown menu */}
                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 glass py-2">
                    <Link
                      href="/billing"
                      className="block px-4 py-2 text-sm text-white/80 hover:text-white hover:bg-white/5 transition-colors"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      Billing
                    </Link>
                    <Link
                      href="/settings"
                      className="block px-4 py-2 text-sm text-white/80 hover:text-white hover:bg-white/5 transition-colors"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      Settings
                    </Link>
                    <button
                      onClick={() => {
                        setUserMenuOpen(false)
                        onLogout?.()
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-white/80 hover:text-white hover:bg-white/5 transition-colors"
                    >
                      Log out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-sm font-medium text-white/80 hover:text-white transition-colors"
                >
                  Log in
                </Link>
                <Link
                  href="/signup"
                  className="text-sm font-medium px-4 py-2 rounded-lg bg-af-purple hover:bg-af-purple/90 transition-colors"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden p-2 text-white/80 hover:text-white"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {menuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden py-4 border-t border-af-card-border">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={clsx(
                  'block py-2 text-sm font-medium transition-colors',
                  isActive(link.href)
                    ? 'text-af-lavender'
                    : 'text-white/70 hover:text-white'
                )}
                onClick={() => setMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            {user ? (
              <>
                <Link
                  href="/billing"
                  className="block py-2 text-sm font-medium text-white/70 hover:text-white"
                  onClick={() => setMenuOpen(false)}
                >
                  Billing
                </Link>
                <Link
                  href="/settings"
                  className="block py-2 text-sm font-medium text-white/70 hover:text-white"
                  onClick={() => setMenuOpen(false)}
                >
                  Settings
                </Link>
                <button
                  onClick={() => {
                    setMenuOpen(false)
                    onLogout?.()
                  }}
                  className="block w-full text-left py-2 text-sm font-medium text-white/70 hover:text-white"
                >
                  Log out
                </button>
              </>
            ) : (
              <div className="flex gap-4 pt-4">
                <Link
                  href="/login"
                  className="text-sm font-medium text-white/80"
                  onClick={() => setMenuOpen(false)}
                >
                  Log in
                </Link>
                <Link
                  href="/signup"
                  className="text-sm font-medium px-4 py-2 rounded-lg bg-af-purple"
                  onClick={() => setMenuOpen(false)}
                >
                  Sign up
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  )
}

export default Navbar

import Link from 'next/link'

interface FooterProps {
  user?: { email?: string } | null
}

/**
 * Footer - Footer component with links
 * Shows copyright, links, and credits
 * Hides auth links when user is logged in
 */
export function Footer({ user }: FooterProps = {}) {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t border-af-card-border bg-af-midnight/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="md:col-span-2">
            <Link href={user ? "/dashboard" : "/"} className="inline-block">
              <h3 className="font-serif text-xl font-bold text-gradient mb-3 hover:opacity-80 transition-opacity">
                AuthorFlow Studios
              </h3>
            </Link>
            <p className="text-sm text-white/60 max-w-sm">
              Transform your manuscripts into studio-ready audiobooks with AI-powered narration.
            </p>
          </div>

          {/* Links - Different for logged in vs logged out */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Product</h4>
            <ul className="space-y-2">
              {user ? (
                <>
                  <li>
                    <Link href="/dashboard" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                      Dashboard
                    </Link>
                  </li>
                  <li>
                    <Link href="/library" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                      My Library
                    </Link>
                  </li>
                  <li>
                    <Link href="/settings" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                      Settings
                    </Link>
                  </li>
                </>
              ) : (
                <>
                  <li>
                    <Link href="/signup" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                      Get Started
                    </Link>
                  </li>
                  <li>
                    <Link href="/login" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                      Log In
                    </Link>
                  </li>
                </>
              )}
            </ul>
          </div>

          {/* Support */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Support</h4>
            <ul className="space-y-2">
              <li>
                <Link href="/pricing" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                  Pricing
                </Link>
              </li>
              <li>
                <Link href="/contact" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                  Contact Us
                </Link>
              </li>
              <li>
                <a href="mailto:support@authorflowstudios.rohimayapublishing.com" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                  Email Support
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Legal Links */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 pt-6 border-t border-af-card-border/50">
          <Link href="/privacy" className="text-sm text-white/50 hover:text-af-lavender transition-colors">
            Privacy Policy
          </Link>
          <Link href="/terms" className="text-sm text-white/50 hover:text-af-lavender transition-colors">
            Terms of Use
          </Link>
          <Link href="/refund" className="text-sm text-white/50 hover:text-af-lavender transition-colors">
            Refund Policy
          </Link>
          <Link href="/cookies" className="text-sm text-white/50 hover:text-af-lavender transition-colors">
            Cookie Policy
          </Link>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-af-card-border flex flex-col md:flex-row justify-between items-center gap-4">
          {/* Copyright */}
          <p className="text-sm text-white/50">
            &copy; {currentYear} AuthorFlow Studios &bull; A Pagade Ventures product
          </p>

          {/* Credits */}
          <p className="text-sm text-white/40">
            Powered by OpenAI, ElevenLabs, and cloud TTS providers
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer

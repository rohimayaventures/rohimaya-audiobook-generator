/**
 * Footer - Footer component with links
 * Shows copyright, links, and credits
 */
export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t border-af-card-border bg-af-midnight/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="md:col-span-2">
            <h3 className="font-serif text-xl font-bold text-gradient mb-3">
              AuthorFlow Studios
            </h3>
            <p className="text-sm text-white/60 max-w-sm">
              Transform your manuscripts into studio-ready audiobooks with AI-powered narration.
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Product</h4>
            <ul className="space-y-2">
              <li>
                <a href="/signup" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                  Get Started
                </a>
              </li>
              <li>
                <a href="/login" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                  Log In
                </a>
              </li>
              <li>
                <a href="/dashboard" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                  Dashboard
                </a>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Support</h4>
            <ul className="space-y-2">
              <li>
                <a href="/contact" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                  Contact Us
                </a>
              </li>
              <li>
                <a href="mailto:support@rohimayapublishing.com" className="text-sm text-white/60 hover:text-af-lavender transition-colors">
                  Email Support
                </a>
              </li>
            </ul>
          </div>
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

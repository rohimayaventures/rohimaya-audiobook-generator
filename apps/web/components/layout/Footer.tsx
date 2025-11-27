/**
 * Footer - Simple footer component
 * Shows copyright and credits
 */
export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t border-af-card-border bg-af-midnight/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
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

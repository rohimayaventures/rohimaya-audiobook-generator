import type { Metadata } from 'next'
import { Inter, Playfair_Display } from 'next/font/google'
import { GradientBackground } from '@/components/ui'
import '@/styles/globals.css'

// Font configurations
const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

const playfair = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-playfair',
  display: 'swap',
})

export const metadata: Metadata = {
  metadataBase: new URL('https://authorflowstudios.rohimayapublishing.com'),
  title: 'AuthorFlow Studios - AI Audiobook Generator',
  description: 'Transform your manuscript into a studio-ready audiobook with AI-powered voices, multi-narrator support, and professional-grade audio quality.',
  keywords: ['audiobook', 'text-to-speech', 'TTS', 'AI', 'manuscript', 'audio', 'book'],
  authors: [{ name: 'AuthorFlow Studios' }],
  openGraph: {
    title: 'AuthorFlow Studios',
    description: 'Transform your manuscript into a studio-ready audiobook',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} ${playfair.variable}`}>
      <body className="font-sans antialiased">
        <GradientBackground>
          {children}
        </GradientBackground>
      </body>
    </html>
  )
}

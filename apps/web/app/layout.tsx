import type { Metadata } from 'next'
import { Inter, Playfair_Display } from 'next/font/google'
import { GradientBackground } from '@/components/ui'
import { Toaster } from 'sonner'
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
  title: {
    default: 'AuthorFlow Studios - AI Audiobook Generator',
    template: '%s | AuthorFlow Studios',
  },
  description: 'Transform your manuscript into a studio-ready audiobook with AI-powered voices, multi-narrator support, and professional-grade audio quality.',
  keywords: ['audiobook', 'text-to-speech', 'TTS', 'AI', 'manuscript', 'audio', 'book', 'author', 'publishing'],
  authors: [{ name: 'AuthorFlow Studios' }],
  creator: 'Pagade Ventures',
  publisher: 'AuthorFlow Studios',
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
    ],
    apple: '/favicon.svg',
  },
  openGraph: {
    title: 'AuthorFlow Studios - AI Audiobook Generator',
    description: 'Transform your manuscript into a studio-ready audiobook with AI-powered voices, multi-narrator support, and professional-grade audio quality.',
    type: 'website',
    siteName: 'AuthorFlow Studios',
    url: 'https://authorflowstudios.rohimayapublishing.com',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AuthorFlow Studios - AI Audiobook Generator',
    description: 'Transform your manuscript into a studio-ready audiobook with AI-powered voices.',
  },
  robots: {
    index: true,
    follow: true,
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
        <Toaster
          position="top-right"
          expand={true}
          richColors
          closeButton
          theme="dark"
          toastOptions={{
            style: {
              background: 'rgba(30, 27, 75, 0.95)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              backdropFilter: 'blur(12px)',
            },
            className: 'text-white',
          }}
        />
      </body>
    </html>
  )
}

import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'AuthorFlow - Audiobook Generator',
  description: 'Turn your manuscript into a studio-ready audiobook in one workflow',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body style={{
        margin: 0,
        padding: 0,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        backgroundColor: '#f5f5f5',
      }}>
        {children}
      </body>
    </html>
  )
}

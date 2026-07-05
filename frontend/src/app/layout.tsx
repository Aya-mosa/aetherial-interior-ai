import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Aetherial — AI Interior Architect',
  description: 'Transform any room with AI-powered interior design. Multi-agent rendering with SDXL + ControlNet.',
  keywords: 'AI interior design, room design, SDXL, ControlNet, furniture placement',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  )
}

import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'M-Motors — Catalogue véhicules',
  description: 'Achat et location longue durée de véhicules d\'occasion — 100% dématérialisé',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  )
}

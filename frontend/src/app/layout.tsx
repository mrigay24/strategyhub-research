import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { TopNav } from '@/components/TopNav'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'StrategyHub — Quant Factor Strategy Research',
    template: '%s | StrategyHub',
  },
  description: '14 systematic factor strategies backtested over 25 years (2000–2024) on 653 S&P 500 stocks. Deep methodology: walk-forward, Monte Carlo, CAPM attribution.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          <TopNav />
          <main className="flex-1">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}

import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'AI Strategy Builder',
  description: 'Describe a trading idea in plain English. Claude maps it to a validated factor strategy and runs 7 quantitative gates against 25 years of data.',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}

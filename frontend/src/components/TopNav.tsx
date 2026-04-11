'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { BarChart3, Sparkles, User, BookOpen } from 'lucide-react'
import { cn } from '@/lib/utils'

export function TopNav() {
  const pathname = usePathname()

  const navItems = [
    { href: '/', label: 'Dashboard', icon: BarChart3 },
    { href: '/findings', label: 'Key Findings', icon: BookOpen },
    { href: '/ai-strategy-builder', label: 'AI Strategy Builder', icon: Sparkles },
  ]

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white">
      <div className="flex h-14 items-center px-6">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2 mr-8">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <span className="font-semibold text-lg">StrategyHub</span>
        </Link>

        {/* Center Nav */}
        <nav className="flex items-center gap-1 flex-1 justify-center">
          {navItems.map((item) => {
            const isActive = pathname === item.href ||
              (item.href === '/' && pathname === '/dashboard')
            const Icon = item.icon

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                )}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        {/* Right User */}
        <button className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center hover:bg-gray-300 transition-colors">
          <User className="w-4 h-4 text-gray-600" />
        </button>
      </div>
    </header>
  )
}

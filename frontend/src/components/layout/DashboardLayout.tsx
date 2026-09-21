import { useState, type ReactNode } from 'react'

import { Header } from './Header'
import { Sidebar } from './Sidebar'

interface DashboardLayoutProps {
  children: ReactNode
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex min-h-screen bg-novera-paper dark:bg-novera-dark-paper text-novera-ink dark:text-novera-dark-ink selection:bg-novera-green selection:text-white font-sans antialiased">
      {/* Operations Rail */}
      <Sidebar mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />
      
      {/* Main Ledger Area with hairline vertical desktop spine */}
      <div className="flex min-w-0 flex-1 flex-col border-l border-novera-rule/50 dark:border-white/5">
        <Header onMenuClick={() => setMobileOpen(true)} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  )
}

import {
  BarChart3,
  FileText,
  LayoutDashboard,
  Sparkles,
  Upload,
  X,
  Zap,
} from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

import { cn } from '../../lib/utils'
import { Button } from '../ui/Button'

const navItems = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { label: 'Upload', icon: Upload, href: '/upload' },
  { label: 'Reports', icon: FileText, href: '/reports' },
  { label: 'AI Analyst', icon: Sparkles, href: '/ai-analyst' },
]

interface SidebarProps {
  mobileOpen?: boolean
  onMobileClose?: () => void
}

export function Sidebar({ mobileOpen = false, onMobileClose }: SidebarProps) {
  const location = useLocation()

  const sidebarContent = (
    <>
      <div className="flex h-16 items-center justify-between border-b border-white/10 px-5">
        <Link to="/dashboard" className="flex items-center gap-3" onClick={onMobileClose}>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl gradient-brand shadow-lg shadow-brand-500/30">
            <Zap className="h-4 w-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">Back-Office</p>
            <p className="text-[10px] font-medium uppercase tracking-widest text-slate-400">
              AI Copilot
            </p>
          </div>
        </Link>
        {onMobileClose && (
          <button
            type="button"
            onClick={onMobileClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition hover:bg-white/10 hover:text-white lg:hidden"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-4">
        <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.15em] text-slate-500">
          Navigation
        </p>
        {navItems.map(({ label, icon: Icon, href }) => {
          const isActive =
            location.pathname === href || (href === '/dashboard' && location.pathname === '/')

          return (
            <Link key={label} to={href} onClick={onMobileClose}>
              <div
                className={cn(
                  'group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'gradient-brand text-white shadow-md shadow-brand-500/25'
                    : 'text-slate-400 hover:bg-white/8 hover:text-white',
                )}
              >
                <Icon
                  className={cn(
                    'h-4 w-4 shrink-0 transition-transform duration-200',
                    !isActive && 'group-hover:scale-110',
                  )}
                />
                {label}
              </div>
            </Link>
          )
        })}
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-white">
            <BarChart3 className="h-4 w-4 text-brand-400" />
            System Status
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse-soft" />
            <p className="text-xs text-slate-400">Phase 1 — Foundation active</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="mt-3 w-full border-white/20 bg-white/5 text-white hover:bg-white/10"
            type="button"
          >
            View changelog
          </Button>
        </div>
      </div>
    </>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col bg-slate-900 lg:flex">
        {sidebarContent}
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm lg:hidden"
          onClick={onMobileClose}
          aria-hidden="true"
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-slate-900 transition-transform duration-300 ease-out lg:hidden',
          mobileOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {sidebarContent}
      </aside>
    </>
  )
}

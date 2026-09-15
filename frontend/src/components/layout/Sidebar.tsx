import {
  ChevronRight,
  FileText,
  GitFork,
  LayoutDashboard,
  LogOut,
  Sparkles,
  Upload,
  User,
  X,
  Zap,
} from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext'
import { cn } from '../../lib/utils'

const navItems = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { label: 'Upload Dataset', icon: Upload, href: '/upload' },
  { label: 'Column Mapping', icon: GitFork, href: '/mapping' },
  { label: 'Intelligence Reports', icon: FileText, href: '/reports' },
  { label: 'AI Analyst', icon: Sparkles, href: '/ai-analyst' },
  { label: 'Executive Profile', icon: User, href: '/profile' },
]

interface SidebarProps {
  mobileOpen?: boolean
  onMobileClose?: () => void
}

export function Sidebar({ mobileOpen = false, onMobileClose }: SidebarProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const userInitials = user?.name
    ? user.name
        .split(' ')
        .map(w => w[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U'

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const sidebarContent = (
    <>
      <div className="flex h-16 items-center justify-between border-b border-white/10 px-5">
        <Link to="/dashboard" className="flex items-center gap-3" onClick={onMobileClose}>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl gradient-brand shadow-lg shadow-brand-500/30">
            <Zap className="h-4 w-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold tracking-tight text-white">Back-Office</p>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-brand-400">
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

      <nav className="flex flex-1 flex-col gap-1.5 p-4">
        <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
          Core Platform
        </p>
        {navItems.map(({ label, icon: Icon, href }) => {
          const isActive =
            location.pathname === href || (href === '/dashboard' && location.pathname === '/')

          return (
            <Link key={label} to={href} onClick={onMobileClose}>
              <div
                className={cn(
                  'group flex items-center justify-between rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'gradient-brand text-white shadow-md shadow-brand-500/25'
                    : 'text-slate-400 hover:bg-white/8 hover:text-white',
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={cn(
                      'h-4 w-4 shrink-0 transition-transform duration-200',
                      !isActive && 'group-hover:scale-110',
                    )}
                  />
                  <span>{label}</span>
                </div>
                {isActive && (
                  <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
                )}
              </div>
            </Link>
          )
        })}
      </nav>

      {/* User profile footer with real user data */}
      <div className="border-t border-white/10 p-3">
        <Link
          to="/profile"
          onClick={onMobileClose}
          className="group flex items-center gap-3 rounded-2xl border border-white/5 bg-white/5 p-2.5 transition-all duration-200 hover:border-brand-500/30 hover:bg-white/10"
        >
          <div className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 via-indigo-600 to-violet-500 font-bold text-white shadow-md shadow-brand-500/25 text-xs">
            <span>{userInitials}</span>
            <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-slate-900 bg-emerald-500" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between">
              <p className="truncate text-xs font-bold text-white group-hover:text-brand-300">
                {user?.name || 'User'}
              </p>
              <ChevronRight className="h-3.5 w-3.5 text-slate-400 opacity-60 transition-all group-hover:opacity-100 group-hover:translate-x-0.5" />
            </div>
            <p className="truncate text-[11px] text-slate-400">{user?.title || 'Analyst'}</p>
          </div>
        </Link>

        <button
          type="button"
          onClick={handleLogout}
          className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl py-2 text-xs font-semibold text-slate-500 transition-all hover:bg-red-500/10 hover:text-red-400"
        >
          <LogOut className="h-3.5 w-3.5" />
          <span>Sign Out</span>
        </button>
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

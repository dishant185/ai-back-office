import {
  ChevronRight,
  Database,
  FileText,
  GitFork,
  LayoutDashboard,
  LogOut,
  Settings,
  Sparkles,
  Upload,
  User,
  X,
} from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext'
import { cn } from '../../lib/utils'
import { SystemStatusIndicator } from './SystemStatusIndicator'

interface NavItem {
  label: string
  icon: React.ComponentType<{ className?: string }>
  href: string
  badge?: string
}

interface NavSection {
  title: string
  items: NavItem[]
}

const navSections: NavSection[] = [
  {
    title: 'Workspace',
    items: [
      { label: 'Overview', icon: LayoutDashboard, href: '/dashboard' },
      { label: 'Datasets', icon: Upload, href: '/upload' },
      { label: 'Reports', icon: FileText, href: '/reports' },
      { label: 'AI Analyst', icon: Sparkles, href: '/ai-analyst' },
    ],
  },
  {
    title: 'Operations',
    items: [
      { label: 'Data Mapping', icon: GitFork, href: '/mapping' },
      { label: 'Audit Activity', icon: Database, href: '/profile' },
    ],
  },
  {
    title: 'Admin',
    items: [
      { label: 'Workspace Settings', icon: Settings, href: '/profile' },
    ],
  },
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
    : 'NV'

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const sidebarContent = (
    <div className="flex h-full flex-col bg-novera-ink text-slate-200 border-r border-novera-rule/20 dark:border-white/10">
      {/* Brand & Workspace Header */}
      <div className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 px-5">
        <Link to="/dashboard" className="flex items-center gap-3 group" onClick={onMobileClose}>
          {/* Novera Monogram Mark */}
          <div className="flex h-8 w-8 items-center justify-center rounded-[2px] bg-novera-deep border border-white/15 text-white font-mono text-sm font-bold shadow-xs">
            <span className="text-novera-green-light">N</span>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-sm font-bold tracking-tight text-white uppercase">
                NOVERA
              </span>
              <span className="inline-block h-1.5 w-1.5 rounded-[1px] bg-novera-green" />
            </div>
            <p className="text-[10px] text-novera-muted leading-tight font-mono truncate max-w-[140px]">
              Verified BI Ledger
            </p>
          </div>
        </Link>
        {onMobileClose && (
          <button
            type="button"
            onClick={onMobileClose}
            className="flex h-7 w-7 items-center justify-center rounded-[2px] text-novera-muted transition hover:bg-white/10 hover:text-white lg:hidden cursor-pointer"
            aria-label="Close menu"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5" aria-label="Operations Rail">
        {navSections.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-2.5 pb-1 text-[10px] font-mono uppercase tracking-wider text-novera-muted/80">
              {section.title}
            </div>
            {section.items.map(({ label, icon: Icon, href, badge }) => {
              const isActive =
                location.pathname === href ||
                (href === '/dashboard' && location.pathname === '/')

              return (
                <Link
                  key={label}
                  to={href}
                  onClick={onMobileClose}
                  className={cn(
                    'group flex items-center justify-between rounded-[2px] px-2.5 py-1.5 text-xs font-medium transition-colors border-l-2',
                    isActive
                      ? 'border-novera-green bg-white/6 text-white'
                      : 'border-transparent text-novera-secondary dark:text-novera-dark-secondary hover:bg-white/4 hover:text-white',
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={cn(
                        'h-3.5 w-3.5 shrink-0 transition-colors',
                        isActive
                          ? 'text-novera-green-light'
                          : 'text-novera-muted group-hover:text-white',
                      )}
                    />
                    <span>{label}</span>
                  </div>
                  {badge ? (
                    <span className="font-mono text-[10px] px-1 py-0.5 rounded-[1px] bg-white/10 text-white">
                      {badge}
                    </span>
                  ) : isActive ? (
                    <span className="h-1 w-1 rounded-[1px] bg-novera-green-light" />
                  ) : null}
                </Link>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Audit System Telemetry */}
      <div className="px-3 pb-2 border-t border-white/10 pt-3">
        <SystemStatusIndicator />
      </div>

      {/* User profile & Workspace Switcher */}
      <div className="border-t border-white/10 p-3">
        <Link
          to="/profile"
          onClick={onMobileClose}
          className="group flex items-center gap-2.5 rounded-[2px] border border-white/5 bg-white/3 p-2 transition-colors hover:border-novera-rule/40 hover:bg-white/6"
        >
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[2px] bg-novera-deep border border-white/10 font-mono text-[11px] font-bold text-novera-green-light">
            <span>{userInitials}</span>
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between">
              <p className="truncate text-xs font-medium text-white group-hover:text-novera-green-light font-sans">
                {user?.name || 'Enterprise User'}
              </p>
              <ChevronRight className="h-3 w-3 text-novera-muted opacity-60 transition-transform group-hover:opacity-100 group-hover:translate-x-0.5" />
            </div>
            <p className="truncate text-[10px] font-mono text-novera-muted">
              {user?.company_name || 'Production Workspace'}
            </p>
          </div>
        </Link>

        <button
          type="button"
          onClick={handleLogout}
          className="mt-2 flex w-full items-center justify-center gap-2 rounded-[2px] py-1.5 text-[11px] font-mono text-novera-muted hover:bg-novera-flag/10 hover:text-novera-flag transition-colors cursor-pointer"
        >
          <LogOut className="h-3 w-3" />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop Operations Rail */}
      <aside className="hidden w-60 shrink-0 flex-col lg:flex">
        {sidebarContent}
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-novera-ink/70 backdrop-blur-xs lg:hidden"
          onClick={onMobileClose}
          aria-hidden="true"
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-68 flex-col transition-transform duration-200 ease-out lg:hidden',
          mobileOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {sidebarContent}
      </aside>
    </>
  )
}

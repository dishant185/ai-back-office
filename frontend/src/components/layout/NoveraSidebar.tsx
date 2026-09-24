import {
  ChevronRight,
  Database,
  FileText,
  GitBranch,
  Layers,
  LayoutDashboard,
  LogOut,
  MessageSquareText,
  PanelLeftClose,
  PanelLeftOpen,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext'
import { cn } from '../../lib/utils'
import { NoveraLogo } from '../brand/NoveraLogo'
import { ProfileAvatar } from '../ui/ProfileAvatar'

export interface NavItem {
  label: string
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>
  href: string
  badge?: string
}

export interface NavSection {
  title: string
  items: NavItem[]
}

const navSections: NavSection[] = [
  {
    title: 'Workspace',
    items: [
      { label: 'Overview', icon: LayoutDashboard, href: '/dashboard' },
      { label: 'Datasets', icon: Database, href: '/upload' },
      { label: 'Workspace', icon: Layers, href: '/workspace' },
      { label: 'Reports', icon: FileText, href: '/reports' },
      { label: 'Analyst', icon: MessageSquareText, href: '/ai-analyst' },
    ],
  },
  {
    title: 'Operations',
    items: [
      { label: 'Data Mapping', icon: GitBranch, href: '/mapping' },
    ],
  },
]

export interface NoveraSidebarProps {
  mobileOpen?: boolean
  onMobileClose?: () => void
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

export function NoveraSidebar({
  mobileOpen = false,
  onMobileClose,
  isCollapsed: controlledCollapsed,
  onToggleCollapse,
}: NoveraSidebarProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [internalCollapsed, setInternalCollapsed] = useState(false)

  const isCollapsed =
    controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed

  const handleToggle = () => {
    if (onToggleCollapse) {
      onToggleCollapse()
    } else {
      setInternalCollapsed(!internalCollapsed)
    }
  }

  const userName = user?.name || 'dishant kanani'

  const handleLogout = () => {
    if (onMobileClose) onMobileClose()
    logout()
    navigate('/login')
  }

  const sidebarBody = (collapsed: boolean) => (
    <div className="flex h-full flex-col bg-[#11181B] text-[#EEF2EE] border-r border-[#2B3538] select-none">
      {/* 1. TOP BRAND AREA */}
      <div
        className={cn(
          'flex shrink-0 items-center border-b border-[#2B3538] transition-all duration-200',
          collapsed ? 'h-16 justify-center px-2' : 'h-16 justify-between px-4'
        )}
      >
        <Link
          to="/dashboard"
          className="flex items-center gap-2.5 overflow-hidden group"
          onClick={onMobileClose}
          aria-label="Novera Home"
        >
          {collapsed ? (
            <NoveraLogo variant="mark" size="md" />
          ) : (
            <div className="flex items-center gap-2">
              <NoveraLogo variant="compact" size="md" theme="dark" />
            </div>
          )}
        </Link>

        {/* Desktop collapse toggle (hidden on mobile) */}
        {!onMobileClose && (
          <button
            type="button"
            onClick={handleToggle}
            className="hidden lg:flex h-6 w-6 items-center justify-center rounded-[2px] text-[#66716C] hover:text-[#EEF2EE] hover:bg-white/[0.06] transition cursor-pointer"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? (
              <PanelLeftOpen className="h-3.5 w-3.5" strokeWidth={1.8} />
            ) : (
              <PanelLeftClose className="h-3.5 w-3.5" strokeWidth={1.8} />
            )}
          </button>
        )}

        {/* Mobile close button */}
        {onMobileClose && (
          <button
            type="button"
            onClick={onMobileClose}
            className="flex h-7 w-7 items-center justify-center rounded-[2px] text-[#66716C] transition hover:bg-white/10 hover:text-white lg:hidden cursor-pointer"
            aria-label="Close navigation menu"
          >
            <X className="h-4 w-4" strokeWidth={1.8} />
          </button>
        )}
      </div>

      {/* 2. NAVIGATION SECTIONS */}
      <nav
        className="flex-1 overflow-y-auto px-2 py-3 space-y-4"
        aria-label="Main Navigation"
      >
        {navSections.map((section) => (
          <div key={section.title} className="space-y-0.5">
            {!collapsed && (
              <div className="px-2.5 pb-1 text-[11px] font-sans font-medium uppercase tracking-wider text-[#66716C]">
                {section.title}
              </div>
            )}
            {section.items.map(({ label, icon: Icon, href, badge }) => {
              const isActive =
                location.pathname === href ||
                (href === '/dashboard' && location.pathname === '/')

              return (
                <Link
                  key={label}
                  to={href}
                  onClick={onMobileClose}
                  title={collapsed ? label : undefined}
                  className={cn(
                    'group relative flex items-center rounded-[2px] text-xs font-medium transition-colors cursor-pointer',
                    collapsed ? 'h-9 justify-center px-1' : 'h-8 justify-between px-2.5',
                    isActive
                      ? 'bg-[#176B50]/10 text-white font-semibold'
                      : 'text-[#AAB5AF] hover:bg-white/[0.04] hover:text-white'
                  )}
                >
                  {/* 2px vertical Novera Green indicator */}
                  {isActive && (
                    <span
                      className="absolute left-0 top-0 bottom-0 w-[2px] bg-[#176B50] rounded-r-[1px]"
                      aria-hidden="true"
                    />
                  )}

                  <div className={cn('flex items-center gap-2.5 min-w-0', collapsed && 'justify-center')}>
                    <Icon
                      strokeWidth={1.85}
                      className={cn(
                        'h-4 w-4 shrink-0 transition-colors',
                        isActive
                          ? 'text-[#4FAF87]'
                          : 'text-[#66716C] group-hover:text-[#EEF2EE]'
                      )}
                    />
                    {!collapsed && <span className="truncate">{label}</span>}
                  </div>

                  {!collapsed && badge && (
                    <span className="font-mono text-[10px] px-1.5 py-0.2 rounded-[1px] bg-white/10 text-white">
                      {badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </div>
        ))}
      </nav>

      {/* 4. USER PROFILE ROW & SIGN OUT */}
      <div className="border-t border-[#2B3538] p-2 space-y-1">
        <button
          type="button"
          onClick={() => {
            if (onMobileClose) onMobileClose()
            navigate('/profile')
          }}
          className={cn(
            'group flex w-full items-center rounded-[2px] transition-colors hover:bg-white/[0.04] cursor-pointer text-left',
            collapsed ? 'justify-center p-1.5' : 'gap-2.5 p-2'
          )}
          aria-label={`User account: ${userName}. Navigate to profile.`}
          title={collapsed ? `${userName} — Account` : undefined}
        >
          {/* Avatar: 32x32 square, 4px radius, #176B50 background, white initials */}
          <ProfileAvatar name={userName} size="md" />

          {!collapsed && (
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <p className="truncate text-xs font-semibold text-[#EEF2EE] group-hover:text-white">
                  {userName}
                </p>
                <ChevronRight className="h-3.5 w-3.5 shrink-0 text-[#66716C] transition-transform group-hover:translate-x-0.5 group-hover:text-[#EEF2EE]" />
              </div>
              <p className="truncate text-[11px] font-sans text-[#66716C] group-hover:text-[#AAB5AF]">
                Account
              </p>
            </div>
          )}
        </button>

        {/* Sign out button at sidebar bottom */}
        <button
          type="button"
          onClick={handleLogout}
          className={cn(
            'flex w-full items-center rounded-[2px] text-xs font-medium text-[#AAB5AF] hover:text-[#D06161] hover:bg-[#D06161]/10 transition-colors cursor-pointer',
            collapsed ? 'justify-center p-2' : 'gap-2 px-2.5 py-1.5'
          )}
          title="Sign out"
          aria-label="Sign out"
        >
          <LogOut className="h-3.5 w-3.5 shrink-0" />
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop Operations Sidebar (width bounded between 240px and 280px, ~260px standard) */}
      <aside
        className={cn(
          'hidden shrink-0 flex-col transition-all duration-200 lg:flex',
          isCollapsed ? 'w-16' : 'w-[260px]'
        )}
      >
        {sidebarBody(isCollapsed)}
      </aside>

      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-[#0E1416]/80 backdrop-blur-xs lg:hidden transition-opacity"
          onClick={onMobileClose}
          aria-hidden="true"
        />
      )}

      {/* Mobile Navigation Drawer */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-[260px] flex-col transition-transform duration-200 ease-out lg:hidden shadow-2xl',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {sidebarBody(false)}
      </aside>
    </>
  )
}

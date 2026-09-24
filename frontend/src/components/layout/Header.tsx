import { useState, useEffect } from 'react'
import { Bell, Menu, Moon, Search, Sun, ShieldCheck } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext'
import { useTheme } from '../../context/ThemeContext'
import { CommandSearch } from '../ui/CommandSearch'
import { ProfileAvatar } from '../ui/ProfileAvatar'

interface HeaderProps {
  onMenuClick?: () => void
}

const pageTitles: Record<string, { section: string; title: string }> = {
  '/dashboard': { section: 'Workspace', title: 'Business Pulse' },
  '/upload': { section: 'Intake', title: 'Datasets' },
  '/mapping': { section: 'Operations', title: 'Data Mapping' },
  '/reports': { section: 'Reporting', title: 'Verified Reports' },
  '/ai-analyst': { section: 'Intelligence', title: 'AI Analyst' },
  '/profile': { section: 'Admin', title: 'Workspace Settings' },
}

export function Header({ onMenuClick }: HeaderProps) {
  const { user } = useAuth()
  const { setTheme, resolvedTheme } = useTheme()
  const location = useLocation()
  const [commandSearchOpen, setCommandSearchOpen] = useState(false)

  // Determine current page title
  const currentPath = location.pathname
  const currentMeta = pageTitles[currentPath] || {
    section: 'Workspace',
    title: 'Business Pulse',
  }

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')
  }

  // Ctrl+K / Cmd+K listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setCommandSearchOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <>
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-novera-rule dark:border-white/10 bg-novera-sheet/95 dark:bg-novera-dark-sheet/95 backdrop-blur-xs px-4 sm:px-6">
        {/* Left: Mobile menu + Breadcrumb */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onMenuClick}
            className="flex h-8 w-8 items-center justify-center rounded-[2px] border border-novera-rule dark:border-white/10 bg-novera-paper dark:bg-novera-dark-paper text-novera-secondary dark:text-novera-dark-secondary transition hover:text-novera-ink dark:hover:text-white lg:hidden cursor-pointer"
            aria-label="Open navigation menu"
          >
            <Menu className="h-4 w-4" />
          </button>
          
          <div className="flex items-center gap-2 text-xs">
            <span className="font-mono text-novera-muted text-[11px]">
              {currentMeta.section}
            </span>
            <span className="text-novera-rule text-[11px]">/</span>
            <span className="font-medium text-novera-ink dark:text-novera-dark-ink">
              {currentMeta.title}
            </span>
          </div>
        </div>

        {/* Center/Right: Search Command Bar + Utilities */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Quick Search Button (opens CommandSearch) */}
          <button
            type="button"
            onClick={() => setCommandSearchOpen(true)}
            className="hidden sm:flex items-center justify-between gap-3 h-8 w-56 lg:w-72 px-2.5 rounded-[2px] border border-novera-rule dark:border-white/10 bg-novera-paper dark:bg-novera-dark-paper text-xs text-novera-muted hover:border-novera-rule-strong dark:hover:border-white/20 transition cursor-pointer"
            aria-label="Open command palette"
          >
            <span className="flex items-center gap-2 truncate">
              <Search className="h-3.5 w-3.5 shrink-0 text-novera-muted" />
              <span className="truncate">Search commands, data...</span>
            </span>
            <kbd className="hidden font-mono text-[10px] px-1 py-0.2 rounded-[1px] bg-novera-sunken dark:bg-white/10 text-novera-secondary dark:text-novera-dark-secondary border border-novera-rule/60 dark:border-transparent md:inline-block">
              Ctrl K
            </kbd>
          </button>

          {/* Trust Status Stamp */}
          <div className="hidden md:flex items-center gap-1.5 px-2 py-1 rounded-[2px] bg-novera-paper dark:bg-white/5 border border-novera-rule/60 dark:border-white/10 text-[10px] font-mono text-novera-secondary dark:text-novera-dark-secondary">
            <ShieldCheck className="h-3 w-3 text-novera-green dark:text-novera-green-light" />
            <span>Audit-Grade Engine</span>
          </div>

          {/* Theme Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            className="flex h-8 w-8 items-center justify-center rounded-[2px] border border-novera-rule dark:border-white/10 bg-novera-paper dark:bg-novera-dark-paper text-novera-secondary dark:text-novera-dark-secondary hover:text-novera-ink dark:hover:text-white transition cursor-pointer"
            aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
            title={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {resolvedTheme === 'dark' ? (
              <Sun className="h-3.5 w-3.5 text-novera-brass" />
            ) : (
              <Moon className="h-3.5 w-3.5 text-novera-secondary" />
            )}
          </button>

          {/* Notifications / Activity */}
          <button
            type="button"
            className="relative flex h-8 w-8 items-center justify-center rounded-[2px] border border-novera-rule dark:border-white/10 bg-novera-paper dark:bg-novera-dark-paper text-novera-secondary dark:text-novera-dark-secondary hover:text-novera-ink dark:hover:text-white transition cursor-pointer"
            aria-label="Audit alerts"
          >
            <Bell className="h-3.5 w-3.5" />
            <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-[1px] bg-novera-green" />
          </button>

          {/* Profile link */}
          <Link
            to="/profile"
            className="flex items-center transition hover:opacity-90 cursor-pointer"
            aria-label="User profile"
            title={user?.name || 'Profile'}
          >
            <ProfileAvatar name={user?.name} size="md" />
          </Link>
        </div>
      </header>

      {/* Global Command Palette Modal */}
      <CommandSearch
        isOpen={commandSearchOpen}
        onClose={() => setCommandSearchOpen(false)}
      />
    </>
  )
}

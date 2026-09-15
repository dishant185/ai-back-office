import { Bell, Menu, Search } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext'

interface HeaderProps {
  onMenuClick?: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { user } = useAuth()

  const userInitials = user?.name
    ? user.name
        .split(' ')
        .map(w => w[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U'

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200/80 glass px-4 sm:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 lg:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-600">
            Operations
          </p>
          <p className="text-sm font-medium text-slate-700">
            Welcome, {user?.name?.split(' ')[0] || 'User'}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <div className="hidden items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-400 shadow-sm transition focus-within:border-brand-300 focus-within:ring-2 focus-within:ring-brand-500/20 md:flex md:w-56 lg:w-72">
          <Search className="h-4 w-4 shrink-0" />
          <input
            type="search"
            placeholder="Search reports, data..."
            className="w-full bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400"
          />
        </div>

        <button
          type="button"
          className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:bg-slate-50"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-brand-500 text-[10px] font-bold text-white">
            2
          </span>
        </button>

        <Link
          to="/profile"
          className="flex h-9 w-9 items-center justify-center rounded-xl gradient-brand text-white shadow-md shadow-brand-500/25 transition hover:brightness-110 active:scale-95 text-[11px] font-bold"
          aria-label="User profile"
          title={user?.name || 'Profile'}
        >
          {userInitials}
        </Link>
      </div>
    </header>
  )
}

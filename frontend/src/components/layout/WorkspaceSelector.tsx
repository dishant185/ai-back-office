import { ChevronDown } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { cn } from '../../lib/utils'

interface WorkspaceSelectorProps {
  className?: string
  collapsed?: boolean
}

export function WorkspaceSelector({ className, collapsed = false }: WorkspaceSelectorProps) {
  const { user } = useAuth()

  // Use dynamic workspace name from user's organization or company
  const workspaceName =
    user?.organization ||
    (user as any)?.company_name ||
    'Production Workspace'

  if (collapsed) {
    return (
      <div
        className={cn(
          'flex h-7 w-7 items-center justify-center rounded-[2px] border border-novera-rule/20 bg-white/5 text-[10px] font-mono font-semibold text-novera-secondary dark:text-novera-dark-secondary',
          className
        )}
        title={workspaceName}
      >
        <span>PW</span>
      </div>
    )
  }

  return (
    <div
      className={cn(
        'group flex h-8 w-full items-center justify-between rounded-[2px] border border-novera-rule/25 dark:border-white/10 bg-white/[0.03] dark:bg-white/[0.02] px-2.5 py-1 text-left transition-colors hover:border-novera-rule/50 dark:hover:border-white/20 select-none cursor-default',
        className
      )}
      aria-label={`Current Workspace: ${workspaceName}`}
    >
      <div className="flex items-center gap-2 min-w-0 pr-1">
        <span className="h-1.5 w-1.5 shrink-0 rounded-[1px] bg-novera-green" />
        <span className="truncate font-sans text-xs font-medium text-slate-800 dark:text-slate-200">
          {workspaceName}
        </span>
      </div>
      <ChevronDown className="h-3 w-3 shrink-0 text-novera-muted opacity-60 transition-opacity group-hover:opacity-100" />
    </div>
  )
}

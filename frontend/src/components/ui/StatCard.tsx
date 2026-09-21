import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '../../lib/utils'
import { Card, CardContent } from './Card'

interface StatCardProps {
  label: string
  value: ReactNode
  icon: LucideIcon
  trend?: { value: string; positive?: boolean }
  iconClassName?: string
  className?: string
}

export function StatCard({
  label,
  value,
  icon: Icon,
  trend,
  iconClassName,
  className,
}: StatCardProps) {
  return (
    <div className={cn('border-b border-novera-rule pb-3 space-y-1.5 bg-novera-paper-sheet p-3.5 rounded-[2px] border border-novera-rule', className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-novera-muted">{label}</span>
        <div
          className={cn(
            'flex h-6 w-6 shrink-0 items-center justify-center rounded-[2px] bg-novera-paper-sunken text-novera-secondary',
            iconClassName,
          )}
        >
          <Icon className="h-3.5 w-3.5" />
        </div>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="font-mono tabular-nums text-2xl font-bold tracking-tight text-novera-ink">
          {value}
        </span>
        {trend && (
          <span
            className={cn(
              'font-mono text-xs font-semibold',
              trend.positive ? 'text-novera-green' : 'text-novera-flag',
            )}
          >
            {trend.value}
          </span>
        )}
      </div>
    </div>
  )
}

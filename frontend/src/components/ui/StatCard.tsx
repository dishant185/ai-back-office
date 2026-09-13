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
    <Card hover className={cn('overflow-hidden', className)}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              {label}
            </p>
            <p className="text-2xl font-bold tracking-tight text-slate-900">{value}</p>
            {trend && (
              <p
                className={cn(
                  'text-xs font-medium',
                  trend.positive ? 'text-emerald-600' : 'text-slate-500',
                )}
              >
                {trend.value}
              </p>
            )}
          </div>
          <div
            className={cn(
              'flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600',
              iconClassName,
            )}
          >
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

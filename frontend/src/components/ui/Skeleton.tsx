import React from 'react'
import { cn } from '../../lib/utils'

export const Skeleton: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  ...props
}) => {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-slate-200/80 dark:bg-slate-800', className)}
      {...props}
    />
  )
}

export const StatCardSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-2xl border border-border bg-surface-raised p-5 shadow-2xs space-y-3"
        >
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-9 w-9 rounded-xl" />
          </div>
          <Skeleton className="h-8 w-32 mt-2" />
          <Skeleton className="h-3 w-40" />
        </div>
      ))}
    </div>
  )
}

export const TableSkeleton: React.FC<{ rows?: number; cols?: number }> = ({
  rows = 5,
  cols = 5,
}) => {
  return (
    <div className="w-full overflow-hidden rounded-2xl border border-border bg-surface-raised shadow-2xs">
      <div className="border-b border-border bg-surface-sunken/50 p-4 flex items-center gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      <div className="divide-y divide-border">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="p-4 flex items-center gap-4">
            {Array.from({ length: cols }).map((_, c) => (
              <Skeleton key={c} className="h-4 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export const CardSkeleton: React.FC<{ className?: string; lines?: number }> = ({
  className,
  lines = 4,
}) => {
  return (
    <div className={cn('rounded-2xl border border-border bg-surface-raised p-6 shadow-2xs space-y-4', className)}>
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <div className="space-y-2.5 pt-2">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton
            key={i}
            className="h-3.5"
            style={{ width: `${Math.max(40, 100 - i * 15)}%` }}
          />
        ))}
      </div>
    </div>
  )
}

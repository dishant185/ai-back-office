import type { ReactNode } from 'react'

import { cn } from '../../lib/utils'

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'brand'

interface BadgeProps {
  children: ReactNode
  className?: string
  variant?: BadgeVariant
  dot?: boolean
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-slate-100 text-slate-700 border-slate-200',
  success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  warning: 'bg-amber-50 text-amber-700 border-amber-200',
  error: 'bg-red-50 text-red-700 border-red-200',
  info: 'bg-sky-50 text-sky-700 border-sky-200',
  brand: 'bg-brand-50 text-brand-700 border-brand-200',
}

export function Badge({ children, className, variant = 'default', dot = false }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold',
        variantClasses[variant],
        className,
      )}
    >
      {dot && (
        <span
          className={cn(
            'h-1.5 w-1.5 rounded-full',
            variant === 'success' && 'bg-emerald-500 animate-pulse-soft',
            variant === 'warning' && 'bg-amber-500 animate-pulse-soft',
            variant === 'error' && 'bg-red-500',
            variant === 'info' && 'bg-sky-500',
            variant === 'brand' && 'bg-brand-500 animate-pulse-soft',
            variant === 'default' && 'bg-slate-400',
          )}
        />
      )}
      {children}
    </span>
  )
}

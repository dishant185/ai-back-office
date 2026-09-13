import type { HTMLAttributes, ReactNode } from 'react'

import { cn } from '../../lib/utils'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  hover?: boolean
}

export function Card({ children, className, hover = false, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-2xl border border-slate-200/80 bg-white shadow-[var(--shadow-card)]',
        hover && 'transition-all duration-300 hover:border-brand-200/60 hover:shadow-[var(--shadow-elevated)]',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ children, className, ...props }: CardProps) {
  return (
    <div className={cn('flex flex-col space-y-1.5 p-6 pb-4', className)} {...props}>
      {children}
    </div>
  )
}

export function CardContent({ children, className, ...props }: CardProps) {
  return (
    <div className={cn('p-6 pt-0', className)} {...props}>
      {children}
    </div>
  )
}

export function CardFooter({ children, className, ...props }: CardProps) {
  return (
    <div
      className={cn('flex items-center border-t border-slate-100 p-6 pt-4', className)}
      {...props}
    >
      {children}
    </div>
  )
}

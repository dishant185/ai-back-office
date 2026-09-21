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
        'rounded-[2px] border border-novera-rule bg-novera-paper-sheet text-novera-ink',
        hover && 'transition-colors duration-150 hover:border-novera-rule-strong',
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
    <div className={cn('flex flex-col space-y-1 p-4 pb-3 border-b border-novera-rule bg-novera-paper-sunken/30', className)} {...props}>
      {children}
    </div>
  )
}

export function CardContent({ children, className, ...props }: CardProps) {
  return (
    <div className={cn('p-4', className)} {...props}>
      {children}
    </div>
  )
}

export function CardFooter({ children, className, ...props }: CardProps) {
  return (
    <div
      className={cn('flex items-center border-t border-novera-rule p-4 pt-3 bg-novera-paper-sunken/20', className)}
      {...props}
    >
      {children}
    </div>
  )
}

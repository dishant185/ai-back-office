import React from 'react'
import type { LucideIcon } from 'lucide-react'
import { Inbox } from 'lucide-react'
import { Button } from './Button'
import { cn } from '../../lib/utils'

interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description: string
  actionLabel?: string
  onAction?: () => void
  secondaryActionLabel?: string
  onSecondaryAction?: () => void
  className?: string
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = Inbox,
  title,
  description,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-8 md:p-12 text-center rounded-2xl border border-dashed border-border bg-surface-raised/50',
        className
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-surface-sunken text-text-muted mb-4 shadow-2xs">
        <Icon className="h-6 w-6 text-brand-500" />
      </div>
      <h3 className="text-base font-semibold text-text-primary mb-1.5">{title}</h3>
      <p className="text-xs text-text-secondary max-w-md leading-relaxed mb-6">
        {description}
      </p>
      {(actionLabel || secondaryActionLabel) && (
        <div className="flex flex-wrap items-center justify-center gap-3">
          {actionLabel && onAction && (
            <Button variant="primary" size="sm" onClick={onAction}>
              {actionLabel}
            </Button>
          )}
          {secondaryActionLabel && onSecondaryAction && (
            <Button variant="secondary" size="sm" onClick={onSecondaryAction}>
              {secondaryActionLabel}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

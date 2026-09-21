import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from './Button'
import { cn } from '../../lib/utils'

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
  isRetrying?: boolean
  className?: string
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to load content',
  message = 'An unexpected error occurred while communicating with the server. Please check your network and try again.',
  onRetry,
  isRetrying = false,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-8 md:p-12 text-center rounded-2xl border border-rose-200 dark:border-rose-900/60 bg-rose-50/50 dark:bg-rose-950/20',
        className
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-100 dark:bg-rose-900/40 text-rose-600 dark:text-rose-400 mb-4 shadow-2xs">
        <AlertCircle className="h-6 w-6" />
      </div>
      <h3 className="text-base font-semibold text-text-primary mb-1.5">{title}</h3>
      <p className="text-xs text-text-secondary max-w-md leading-relaxed mb-6">
        {message}
      </p>
      {onRetry && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onRetry}
          disabled={isRetrying}
          className="gap-2"
        >
          <RefreshCw className={cn('h-3.5 w-3.5', isRetrying && 'animate-spin')} />
          <span>{isRetrying ? 'Retrying...' : 'Try Again'}</span>
        </Button>
      )}
    </div>
  )
}

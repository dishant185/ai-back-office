import React from 'react'
import { cn } from '../../lib/utils'

interface MetricValueProps {
  label: string
  value: string | number
  subtext?: string
  trend?: {
    value: string
    isPositive?: boolean
  }
  status?: 'verified' | 'ai_assisted' | 'flagged' | 'neutral'
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

export const MetricValue: React.FC<MetricValueProps> = ({
  label,
  value,
  subtext,
  trend,
  status = 'verified',
  className,
  size = 'md',
}) => {
  return (
    <div className={cn('flex flex-col border-b border-novera-rule pb-3 space-y-1', className)}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-novera-muted">{label}</span>
        {status === 'verified' && (
          <span className="h-1.5 w-1.5 rounded-[1px] bg-novera-green" title="Verified dataset calculation" />
        )}
        {status === 'ai_assisted' && (
          <span className="h-1.5 w-1.5 rounded-[1px] bg-novera-brass" title="AI-assisted metric" />
        )}
        {status === 'flagged' && (
          <span className="h-1.5 w-1.5 rounded-[1px] bg-novera-flag" title="Discrepancy flagged" />
        )}
      </div>
      <div className="flex items-baseline gap-2">
        <span
          className={cn(
            'font-mono tabular-nums font-semibold tracking-tight text-novera-ink',
            size === 'lg' && 'text-3xl',
            size === 'md' && 'text-2xl',
            size === 'sm' && 'text-lg'
          )}
        >
          {value}
        </span>
        {trend && (
          <span
            className={cn(
              'font-mono text-xs font-medium',
              trend.isPositive ? 'text-novera-green' : 'text-novera-flag'
            )}
          >
            {trend.value}
          </span>
        )}
      </div>
      {subtext && <p className="text-[11px] text-novera-secondary">{subtext}</p>}
    </div>
  )
}

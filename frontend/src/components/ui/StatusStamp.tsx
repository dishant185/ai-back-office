import React from 'react'
import { cn } from '../../lib/utils'

export type NoveraStatus =
  | 'VERIFIED'
  | 'AI_ASSISTED'
  | 'WITHHELD'
  | 'UNAVAILABLE'
  | 'AI_GENERATED_GROUNDED'
  | 'VERIFIED_ANALYTICS_ONLY'
  | 'AI_NOT_CONFIGURED'
  | 'AI_VALIDATION_FAILED'
  | 'AI_GENERATION_UNAVAILABLE'
  | string

interface StatusStampProps {
  status?: NoveraStatus
  className?: string
  compact?: boolean
  label?: string
}

export const StatusStamp: React.FC<StatusStampProps> = ({
  status = 'VERIFIED',
  className,
  compact = false,
  label,
}) => {
  const norm = (status || '').toUpperCase()

  let squareColor = 'bg-novera-muted text-novera-muted'
  let textColor = 'text-novera-secondary'
  let defaultText = 'AI unavailable'
  let description = 'AI assistance is unavailable or offline.'

  if (norm === 'VERIFIED' || norm === 'VERIFIED_ANALYTICS_ONLY') {
    squareColor = 'bg-novera-green'
    textColor = 'text-novera-green'
    defaultText = 'Verified'
    description = 'Deterministic calculation audited directly against dataset rows.'
  } else if (norm === 'AI_ASSISTED' || norm === 'AI_GENERATED_GROUNDED') {
    squareColor = 'bg-novera-brass'
    textColor = 'text-novera-brass'
    defaultText = 'AI-assisted'
    description = 'LLM narrative synthesized from verified numerical calculations.'
  } else if (norm === 'WITHHELD' || norm === 'AI_VALIDATION_FAILED') {
    squareColor = 'bg-novera-flag'
    textColor = 'text-novera-flag'
    defaultText = 'Withheld'
    description = 'Output failed validation safeguards and was withheld to prevent hallucination.'
  } else if (norm === 'AI_NOT_CONFIGURED' || norm === 'AI_GENERATION_UNAVAILABLE' || norm === 'UNAVAILABLE') {
    squareColor = 'bg-novera-muted'
    textColor = 'text-novera-muted'
    defaultText = 'AI unavailable'
    description = 'Analytical engine is operating without active LLM provider.'
  }

  const displayText = label || defaultText

  return (
    <span
      role="status"
      title={description}
      className={cn(
        'inline-flex items-center gap-1.5 font-mono text-xs font-semibold tracking-tight uppercase select-none',
        textColor,
        className
      )}
    >
      <span
        aria-hidden="true"
        className={cn('shrink-0 rounded-[1px]', compact ? 'h-2 w-2' : 'h-2.5 w-2.5', squareColor)}
      />
      <span>{displayText}</span>
    </span>
  )
}

import React from 'react'
import { StatusStamp, type NoveraStatus } from './StatusStamp'

export type VerificationStatus = NoveraStatus

interface VerificationBadgeProps {
  status?: VerificationStatus
  className?: string
  size?: 'sm' | 'md'
}

export const VerificationBadge: React.FC<VerificationBadgeProps> = ({
  status = 'VERIFIED',
  className,
  size = 'md',
}) => {
  return (
    <StatusStamp
      status={status}
      className={className}
      compact={size === 'sm'}
    />
  )
}

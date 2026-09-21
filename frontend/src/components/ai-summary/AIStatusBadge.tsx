import React from 'react'
import { VerificationBadge, type VerificationStatus } from '../ui/VerificationBadge'

export type SummaryStatusType = VerificationStatus

export const AIStatusBadge: React.FC<{ status?: string; className?: string }> = (props) => {
  return <VerificationBadge {...props} />
}

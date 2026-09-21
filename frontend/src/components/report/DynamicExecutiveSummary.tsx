import React from 'react'
import { ExecutiveSummary } from '../ai-summary/ExecutiveSummary'
import type { DynamicSummarySectionData } from '../../types/report'

export interface DynamicExecutiveSummaryData {
  title?: string
  overview?: string | { text: string; evidence_ids?: string[] }
  sections?: DynamicSummarySectionData[]
  recommendations?: (string | { content?: string; text?: string; evidence_ids?: string[]; confidence?: string })[]
  limitations?: (string | { content?: string; text?: string })[]
  status?: string
  status_label?: string
  verified_claims?: string[]
  verified_evidence?: any
  report_type?: string
  dataset_version?: number
  report_version?: number
}

interface DynamicExecutiveSummaryProps {
  summaryData?: DynamicExecutiveSummaryData | null
  isLoading?: boolean
  onRegenerate?: () => void
  onViewEvidence?: () => void
  reportTitle?: string
  datasetName?: string
  datasetVersion?: number
  reportVersion?: number
}

export const DynamicExecutiveSummary: React.FC<DynamicExecutiveSummaryProps> = (props) => {
  return <ExecutiveSummary {...props} />
}

import React, { useState } from 'react'
import { Sparkles } from 'lucide-react'
import { Card, CardContent, CardHeader } from '../ui/Card'
import { SummaryHeader } from './SummaryHeader'
import { SummaryOverview } from './SummaryOverview'
import { SummarySection } from './SummarySection'
import { SummaryRecommendations } from './SummaryRecommendations'
import { SummaryLimitations } from './SummaryLimitations'
import { EvidenceViewer } from './EvidenceViewer'

export interface ExecutiveSummaryProps {
  summaryData?: {
    title?: string
    overview?: string | { text: string; evidence_ids?: string[] }
    sections?: Array<{
      section_id?: string
      title: string
      type?: string
      content: string
      evidence_ids?: string[]
      validated?: boolean
    }>
    recommendations?: Array<string | { text?: string; content?: string; evidence_ids?: string[] }>
    limitations?: Array<string | { text?: string; content?: string; evidence_ids?: string[] }>
    status?: string
    status_label?: string
    verified_evidence?: Record<string, any>
  } | null
  isLoading?: boolean
  reportTitle?: string
  datasetName?: string
  datasetVersion?: number
  reportVersion?: number
  onRegenerate?: () => void
}

export const ExecutiveSummary: React.FC<ExecutiveSummaryProps> = ({
  summaryData,
  isLoading = false,
  reportTitle,
  datasetName,
  datasetVersion = 1,
  reportVersion = 1,
  onRegenerate,
}) => {
  const [copied, setCopied] = useState(false)
  const [isExpanded, setIsExpanded] = useState(true)
  const [showEvidence, setShowEvidence] = useState(false)

  if (isLoading) {
    return (
      <Card className="border-indigo-200 bg-gradient-to-r from-indigo-50/80 via-white to-indigo-50/80 p-5 rounded-2xl shadow-xs animate-pulse">
        <div className="flex items-center gap-3.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-xs">
            <Sparkles className="h-4 w-4 animate-spin" />
          </div>
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-indigo-950">Preparing AI Executive Summary</span>
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-indigo-500 animate-ping" />
            </div>
            <p className="text-[11px] text-indigo-600">
              Analyzing verified metrics & validating claim-level grounding for{' '}
              <span className="font-semibold">{reportTitle || 'Current Report'}</span>...
            </p>
          </div>
        </div>
      </Card>
    )
  }

  if (!summaryData) return null

  const {
    title = reportTitle ? `${reportTitle} Executive Summary` : 'AI Executive Summary',
    overview,
    sections = [],
    recommendations = [],
    limitations = [],
    status = 'AI_GENERATED_GROUNDED',
    verified_evidence = {},
  } = summaryData

  const overviewText = typeof overview === 'string' ? overview : overview?.text || ''
  const overviewEids = typeof overview === 'object' && overview?.evidence_ids ? overview.evidence_ids : []

  // Avoid visual and clipboard repetition if a section repeats the overview
  const cleanOverviewCompare = overviewText
    ? overviewText
        .replace("AI narrative could not be verified against the report's data and was withheld. Showing verified report analytics.", '')
        .trim()
        .toLowerCase()
    : ''

  const visibleSections = sections.filter((sec) => {
    const content = sec.content?.trim()
    if (!content) return false
    const normContent = content.toLowerCase()
    if (cleanOverviewCompare && (cleanOverviewCompare === normContent || cleanOverviewCompare.includes(normContent))) {
      return false
    }
    return true
  })

  const handleCopy = () => {
    const lines: string[] = [`AI EXECUTIVE SUMMARY — ${title}`]
    if (overviewText) {
      lines.push('', overviewText)
    }
    visibleSections.forEach((sec) => {
      lines.push('', `[${sec.title.toUpperCase()}]`, sec.content)
    })
    if (recommendations.length > 0) {
      lines.push('', '[RECOMMENDATIONS]')
      recommendations.forEach((rec, idx) => {
        const t = typeof rec === 'string' ? rec : rec.text || rec.content || ''
        lines.push(`${idx + 1}. ${t}`)
      })
    }
    if (limitations.length > 0) {
      lines.push('', '[LIMITATIONS]')
      limitations.forEach((lim) => {
        const t = typeof lim === 'string' ? lim : lim.text || lim.content || ''
        lines.push(`• ${t}`)
      })
    }

    void navigator.clipboard.writeText(lines.join('\n'))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <>
      <Card className="border-indigo-200/90 bg-gradient-to-br from-indigo-50/50 via-white to-indigo-50/30 shadow-xs animate-slide-up print:border-indigo-300">
        <CardHeader className="pb-0 border-none">
          <SummaryHeader
            title={title}
            status={status}
            isExpanded={isExpanded}
            copied={copied}
            isLoading={isLoading}
            onToggleExpand={() => setIsExpanded(!isExpanded)}
            onCopy={handleCopy}
            onViewEvidence={() => setShowEvidence(true)}
            onRegenerate={onRegenerate}
          />
        </CardHeader>

        {isExpanded && (
          <CardContent className="pt-4 space-y-3.5">
            {/* Short Executive Overview */}
            <SummaryOverview overviewText={overviewText} evidenceIds={overviewEids} />

            {/* Dynamic Sections in evidence-derived order */}
            {visibleSections.length > 0 && (
              <div className="space-y-3">
                {visibleSections.map((section, idx) => (
                  <SummarySection key={idx} section={section} />
                ))}
              </div>
            )}

            {/* Optional Recommendations */}
            <SummaryRecommendations recommendations={recommendations} />

            {/* Optional Limitations */}
            <SummaryLimitations limitations={limitations} />

            {/* Audit Scope Footer */}
            {datasetName && (
              <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-indigo-50">
                <span>Scoped to {datasetName} (v{datasetVersion})</span>
                <span>Report v{reportVersion}</span>
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Evidence Audit Trail Modal */}
      <EvidenceViewer
        isOpen={showEvidence}
        onClose={() => setShowEvidence(false)}
        evidence={verified_evidence}
        datasetName={datasetName}
        datasetVersion={datasetVersion}
      />
    </>
  )
}

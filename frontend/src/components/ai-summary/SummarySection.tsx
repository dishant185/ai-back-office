import React from 'react'
import { CheckCircle2, TrendingUp, BarChart2, ShieldAlert } from 'lucide-react'

interface SummarySectionProps {
  section: {
    section_id?: string
    title: string
    type?: string
    content: string
    evidence_ids?: string[]
    validated?: boolean
  }
}

export const SummarySection: React.FC<SummarySectionProps> = ({ section }) => {
  const { title, type = 'finding', content, evidence_ids = [] } = section

  // Rule #38: Do not render empty content
  if (!content || !content.trim()) return null

  const getSectionIcon = () => {
    switch (type.toLowerCase()) {
      case 'trend':
        return <TrendingUp className="h-3.5 w-3.5 text-blue-600" />
      case 'comparison':
        return <BarChart2 className="h-3.5 w-3.5 text-indigo-600" />
      case 'quality':
        return <ShieldAlert className="h-3.5 w-3.5 text-amber-600" />
      default:
        return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
    }
  }

  return (
    <div className="rounded-xl border border-slate-200/80 bg-white p-4 space-y-2 shadow-2xs hover:border-indigo-200 transition-colors">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {getSectionIcon()}
          <h4 className="text-xs sm:text-sm font-semibold text-slate-900 tracking-tight">{title}</h4>
        </div>
        {evidence_ids.length > 0 && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
            {evidence_ids.length} verified {evidence_ids.length === 1 ? 'evidence point' : 'evidence points'}
          </span>
        )}
      </div>

      <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-normal">{content}</p>
    </div>
  )
}

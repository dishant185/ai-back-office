import React from 'react'
import { Info } from 'lucide-react'

interface LimitationItem {
  text?: string
  content?: string
  evidence_ids?: string[]
}

interface SummaryLimitationsProps {
  limitations?: (string | LimitationItem)[]
}

export const SummaryLimitations: React.FC<SummaryLimitationsProps> = ({ limitations = [] }) => {
  if (!limitations || limitations.length === 0) return null

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 space-y-1.5 shadow-2xs">
      <div className="flex items-center gap-2 text-slate-700 font-semibold text-xs">
        <Info className="h-3.5 w-3.5 text-slate-500" />
        <span>Evaluated Scope & Data Limitations</span>
      </div>
      <ul className="list-disc pl-5 space-y-1 text-[11px] text-slate-600">
        {limitations.map((lim, idx) => {
          const text = typeof lim === 'string' ? lim : lim.text || lim.content || ''
          return <li key={idx}>{text}</li>
        })}
      </ul>
    </div>
  )
}

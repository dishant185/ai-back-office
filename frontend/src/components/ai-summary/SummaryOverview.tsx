import React from 'react'
import { ShieldCheck, ShieldAlert } from 'lucide-react'

interface SummaryOverviewProps {
  overviewText: string
  evidenceIds?: string[]
}

const FALLBACK_NOTICE =
  "AI narrative could not be verified against the report's data and was withheld. Showing verified report analytics."

export const SummaryOverview: React.FC<SummaryOverviewProps> = ({ overviewText, evidenceIds = [] }) => {
  if (!overviewText) return null

  const hasFallbackNotice = overviewText.includes(FALLBACK_NOTICE)
  const cleanOverviewText = hasFallbackNotice
    ? overviewText.replace(FALLBACK_NOTICE, '').trim()
    : overviewText

  return (
    <div className="space-y-3">
      {hasFallbackNotice && (
        <div className="flex items-start gap-2.5 rounded-xl border border-amber-200/80 bg-amber-50/70 p-3.5 text-xs text-amber-900 leading-snug shadow-2xs">
          <ShieldAlert className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-semibold text-amber-950">Safety Safeguard Active: </span>
            <span>
              AI narrative was withheld to prevent ungrounded figures. Presenting 100% verified analytical calculations.
            </span>
          </div>
        </div>
      )}

      {cleanOverviewText && (
        <div className="rounded-xl border border-indigo-100/70 bg-indigo-50/20 p-4 space-y-2 shadow-2xs">
          <div className="text-xs sm:text-sm text-slate-800 leading-relaxed font-normal">
            {cleanOverviewText}
          </div>
          {evidenceIds && evidenceIds.length > 0 && (
            <div className="flex items-center gap-1.5 pt-1">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-white text-indigo-700 border border-indigo-200/70 shadow-2xs">
                <ShieldCheck className="h-3 w-3 text-indigo-600" />
                <span>Grounded in {evidenceIds.length} verified {evidenceIds.length === 1 ? 'fact' : 'facts'}</span>
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

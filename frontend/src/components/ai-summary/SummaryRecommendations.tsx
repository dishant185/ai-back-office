import React from 'react'
import { Lightbulb, CheckCircle2 } from 'lucide-react'

interface RecommendationItem {
  text?: string
  content?: string
  evidence_ids?: string[]
  reason?: string
}

interface SummaryRecommendationsProps {
  recommendations?: (string | RecommendationItem)[]
}

export const SummaryRecommendations: React.FC<SummaryRecommendationsProps> = ({ recommendations = [] }) => {
  // Rule #38: Do not render empty recommendations
  if (!recommendations || recommendations.length === 0) return null

  const validRecs = recommendations
    .map((rec) => {
      const text = typeof rec === 'string' ? rec : rec.text || rec.content || ''
      const evIds = typeof rec === 'object' && rec.evidence_ids ? rec.evidence_ids : []
      const reason = typeof rec === 'object' && rec.reason ? rec.reason : ''
      return { text, evIds, reason }
    })
    .filter((r) => r.text && r.text.trim().length > 0)

  if (validRecs.length === 0) return null

  return (
    <div className="rounded-xl border border-indigo-100/80 bg-white p-4 space-y-2.5 shadow-2xs">
      <div className="flex items-center gap-2 text-indigo-950 font-semibold text-xs uppercase tracking-wider">
        <Lightbulb className="h-4 w-4 text-indigo-600" />
        <span>Evidence-Grounded Recommendations</span>
      </div>
      <ul className="space-y-2.5 text-xs text-slate-700">
        {validRecs.map((rec, idx) => (
          <li key={idx} className="flex items-start gap-2.5">
            <span className="font-bold text-indigo-600 shrink-0 mt-0.5">{idx + 1}.</span>
            <div className="space-y-1">
              <span className="leading-relaxed font-medium text-slate-800">{rec.text}</span>
              {rec.reason && (
                <p className="text-[11px] text-slate-500 italic">{rec.reason}</p>
              )}
              {rec.evIds.length > 0 && (
                <div className="flex items-center gap-1.5 pt-0.5">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                    <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                    <span>Validated by {rec.evIds.length} evidence {rec.evIds.length === 1 ? 'item' : 'items'}</span>
                  </span>
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

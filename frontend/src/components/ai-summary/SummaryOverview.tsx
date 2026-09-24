import React from 'react'
import { ShieldCheck, ShieldAlert } from 'lucide-react'

interface SummaryOverviewProps {
  overviewText: string
  evidenceIds?: string[]
  datasetOverview?: string
  highlights?: string[]
  overall?: string
}

const FALLBACK_NOTICE =
  "AI narrative could not be verified against the report's data and was withheld. Showing verified report analytics."

function parseSalesStyleOverview(text: string) {
  const parts = text.split('\n\n').map((p) => p.trim()).filter(Boolean)
  let overview = ''
  const bullets: string[] = []
  let overall = ''

  for (const part of parts) {
    if (part.startsWith('Overall:')) {
      overall = part.replace(/^Overall:\s*/, '').trim()
    } else if (part.includes('\n- ') || part.includes('\n• ') || part.startsWith('- ') || part.startsWith('• ')) {
      const lines = part.split('\n').map((l) => l.trim()).filter(Boolean)
      for (const line of lines) {
        if (line.startsWith('- ') || line.startsWith('• ')) {
          bullets.push(line.replace(/^[-•]\s*/, '').trim())
        } else if (line.startsWith('Overall:')) {
          overall = line.replace(/^Overall:\s*/, '').trim()
        } else if (!overview) {
          overview = line
        }
      }
    } else if (!overview) {
      overview = part
    } else if (part.toLowerCase().startsWith('overall')) {
      overall = part.replace(/^overall:?\s*/i, '').trim()
    }
  }

  return { overview, bullets, overall }
}

export const SummaryOverview: React.FC<SummaryOverviewProps> = ({
  overviewText,
  evidenceIds = [],
  datasetOverview,
  highlights,
  overall,
}) => {
  if (!overviewText && !datasetOverview && (!highlights || highlights.length === 0) && !overall) {
    return null
  }

  const hasFallbackNotice = overviewText?.includes(FALLBACK_NOTICE) || false
  const cleanOverviewText = hasFallbackNotice
    ? overviewText.replace(FALLBACK_NOTICE, '').trim()
    : overviewText || ''

  const parsed = parseSalesStyleOverview(cleanOverviewText)
  const displayOverview = datasetOverview || parsed.overview
  const displayBullets = (highlights && highlights.length > 0) ? highlights : parsed.bullets
  const displayOverall = overall || parsed.overall

  const isStructured = displayBullets.length > 0 || !!displayOverall

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

      {isStructured ? (
        <div className="rounded-xl border border-indigo-100/70 bg-indigo-50/20 p-4 space-y-3.5 shadow-2xs">
          {/* A. Dataset Overview */}
          {displayOverview && (
            <p className="text-xs sm:text-sm font-medium text-slate-800 leading-relaxed">
              {displayOverview}
            </p>
          )}

          {/* B. Dynamic Verified Highlights */}
          {displayBullets.length > 0 && (
            <ul className="space-y-1.5 py-1">
              {displayBullets.map((bullet, idx) => {
                let label = ''
                let val = bullet
                if (bullet.includes('–')) {
                  const split = bullet.split('–')
                  label = split[0].trim()
                  val = split.slice(1).join('–').trim()
                } else if (bullet.includes(':')) {
                  const split = bullet.split(':')
                  label = split[0].trim()
                  val = split.slice(1).join(':').trim()
                }

                return (
                  <li key={idx} className="flex items-baseline gap-2.5 text-xs sm:text-sm text-slate-700">
                    <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-600 relative top-[-1px]" />
                    <span>
                      {label ? <span className="font-semibold text-slate-900">{label}: </span> : null}
                      <span>{val}</span>
                    </span>
                  </li>
                )
              })}
            </ul>
          )}

          {/* C. Overall Factual Interpretation */}
          {displayOverall && (
            <div className="rounded-lg bg-emerald-50/50 border border-emerald-100/80 p-3 text-xs sm:text-sm text-slate-700 leading-relaxed">
              <span className="font-semibold text-slate-900">Overall: </span>
              <span>{displayOverall.replace(/^Overall:\s*/, '')}</span>
            </div>
          )}

          {/* Grounding Badge */}
          {evidenceIds && evidenceIds.length > 0 && (
            <div className="flex items-center gap-1.5 pt-1">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-white text-indigo-700 border border-indigo-200/70 shadow-2xs">
                <ShieldCheck className="h-3 w-3 text-indigo-600" />
                <span>Grounded in {evidenceIds.length} verified {evidenceIds.length === 1 ? 'fact' : 'facts'}</span>
              </span>
            </div>
          )}
        </div>
      ) : cleanOverviewText ? (
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
      ) : null}
    </div>
  )
}


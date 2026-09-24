import { AlertTriangle, CheckCircle2, Sparkles } from 'lucide-react'
import type { ExecutiveSummary } from '../../types/report'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardHeader } from '../ui/Card'

interface ExecutiveSummaryCardProps {
  summary: ExecutiveSummary
}

export function ExecutiveSummaryCard({ summary }: ExecutiveSummaryCardProps) {
  const sentimentVariant =
    summary.sentiment === 'positive'
      ? 'success'
      : summary.sentiment === 'cautionary'
        ? 'warning'
        : 'info'

  return (
    <Card className="border-brand-100 bg-gradient-to-br from-white via-brand-50/20 to-white shadow-sm">
      <CardHeader className="pb-3 border-b border-slate-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-100 text-brand-600">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-900">Executive Summary</h2>
              <p className="text-xs text-slate-500">Autonomous intelligence and key takeaways</p>
            </div>
          </div>
          <Badge variant={sentimentVariant} dot>
            {summary.sentiment === 'positive'
              ? 'Positive Trajectory'
              : summary.sentiment === 'cautionary'
                ? 'Action Required'
                : 'Balanced State'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-4 space-y-4">
        {summary.dataset_overview ? (
          <div className="space-y-3.5">
            <p className="text-sm font-medium leading-relaxed text-slate-800">{summary.dataset_overview}</p>
            {summary.highlights && summary.highlights.length > 0 && (
              <ul className="space-y-1.5 py-1">
                {summary.highlights.map((h, i) => {
                  let label = ''
                  let val = h
                  if (h.includes('–')) {
                    const split = h.split('–')
                    label = split[0].trim()
                    val = split.slice(1).join('–').trim()
                  } else if (h.includes(':')) {
                    const split = h.split(':')
                    label = split[0].trim()
                    val = split.slice(1).join(':').trim()
                  }
                  return (
                    <li key={i} className="flex items-baseline gap-2.5 text-xs sm:text-sm text-slate-700">
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
            {summary.overall && (
              <div className="rounded-lg bg-emerald-50/50 border border-emerald-100/80 p-3 text-xs sm:text-sm text-slate-700 leading-relaxed">
                <span className="font-semibold text-slate-900">Overall: </span>
                <span>{summary.overall.replace(/^Overall:\s*/, '')}</span>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm leading-relaxed text-slate-700 whitespace-pre-line">{summary.overview}</p>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          {(!summary.highlights || summary.highlights.length === 0) && summary.key_highlights?.length > 0 && (
            <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-800 uppercase tracking-wider mb-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                Operational Highlights
              </div>
              <ul className="space-y-1.5 text-xs text-slate-700">
                {summary.key_highlights.map((h, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {summary.critical_findings?.length > 0 && (
            <div className="rounded-xl border border-amber-100 bg-amber-50/50 p-4">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-800 uppercase tracking-wider mb-2">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
                Critical Observations & Risk
              </div>
              <ul className="space-y-1.5 text-xs text-slate-700">
                {summary.critical_findings.map((f, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

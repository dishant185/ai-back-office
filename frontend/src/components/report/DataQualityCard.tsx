import { AlertCircle, CheckCircle2, ShieldCheck, XCircle } from 'lucide-react'
import type { DataQuality } from '../../types/report'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardHeader } from '../ui/Card'

interface DataQualityCardProps {
  quality: DataQuality
}

export function DataQualityCard({ quality }: DataQualityCardProps) {
  const isHealthy = quality.score >= 85
  const isWarning = quality.score >= 65 && quality.score < 85

  return (
    <Card className="shadow-sm border-slate-200">
      <CardHeader className="pb-3 border-b border-slate-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Data Quality & Health Audit</h3>
              <p className="text-xs text-slate-500">Hygiene verification and integrity metrics</p>
            </div>
          </div>
          <Badge variant={isHealthy ? 'success' : isWarning ? 'warning' : 'error'} dot>
            Score: {quality.score}/100
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-4 space-y-4">
        {/* Metric bars */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
            <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
              Field Completeness
            </span>
            <div className="mt-1 text-lg font-bold text-slate-900">
              {quality.completeness_pct ?? 100}%
            </div>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
            <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
              Missing Cells
            </span>
            <div className="mt-1 text-lg font-bold text-slate-900">
              {(quality.missing_cells ?? 0).toLocaleString()}
            </div>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
            <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
              Duplicate Rows
            </span>
            <div className="mt-1 text-lg font-bold text-slate-900">
              {(quality.duplicate_rows ?? 0).toLocaleString()}
              {quality.duplicate_pct != null && quality.duplicate_rows > 0 ? (
                <span className="text-xs font-normal text-slate-500 ml-1.5">
                  ({quality.duplicate_pct.toFixed(1)}%)
                </span>
              ) : null}
            </div>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
            <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
              Records Audited
            </span>
            <div className="mt-1 text-lg font-bold text-slate-900">
              {(quality.total_rows ?? 0).toLocaleString()}
            </div>
          </div>
        </div>

        {/* Issues list */}
        {quality.issues?.length > 0 ? (
          <div className="space-y-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Integrity Findings
            </span>
            <div className="space-y-1.5">
              {quality.issues.map((issue, idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-2 rounded-lg p-2.5 text-xs ${
                    issue.severity === 'critical'
                      ? 'bg-red-50 text-red-800'
                      : issue.severity === 'warning'
                        ? 'bg-amber-50 text-amber-800'
                        : 'bg-slate-50 text-slate-700'
                  }`}
                >
                  {issue.severity === 'critical' ? (
                    <XCircle className="h-4 w-4 shrink-0 text-red-500 mt-0.5" />
                  ) : issue.severity === 'warning' ? (
                    <AlertCircle className="h-4 w-4 shrink-0 text-amber-500 mt-0.5" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-slate-400 mt-0.5" />
                  )}
                  <div>
                    {issue.column && (
                      <span className="font-semibold mr-1">[{issue.column}]</span>
                    )}
                    <span>{issue.description}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-lg bg-emerald-50/60 p-3 text-xs text-emerald-800">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            <span>All columns verified with 100% integrity. Zero critical discrepancies detected.</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
